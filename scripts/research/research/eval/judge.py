"""Grade the pooled top results of every provider with a blind LLM judge."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click

from research._fetch import fetch_markdown
from research._secrets import read_secret
from research.eval import cli
from research.eval._data import (
    JUDGMENTS,
    PAGES,
    QUERIES,
    append_jsonl,
    read_jsonl,
    url_key,
)
from research.eval._providers import ProviderError, post_json
from research.eval.report import JUDGE_MODEL, latest_results

POOL_DEPTH = 5
_PAGE_CHARS = 6000
_NANO_GPT = "https://nano-gpt.com/api/v1/chat/completions"

_RUBRIC = """\
You grade one web page for a research agent. The agent was given the task below and sent the \
search query below. Judge only the page, not how it was found.

Grades:
2 = directly answers the query or is the primary source the task asks for (official docs, the \
exact issue or thread, the authoritative page).
1 = on topic and partly useful: related background, a secondary source, or an answer to a \
neighbouring question.
0 = off topic, spam, a login or error page, or too generic to help.

Reply with JSON only: {"grade": 0|1|2, "reason": "<one short sentence>"}"""


def _pool(records: list[dict], results: dict[str, dict[str, dict]]) -> dict[tuple[str, str], dict]:
    """Return each query's unique top results across providers, keyed by (query id, URL key)."""
    pool: dict[tuple[str, str], dict] = {}
    for record in records:
        for rows in results.values():
            row = rows.get(record["id"])
            if not row:
                continue
            for result in row["results"][:POOL_DEPTH]:
                key = (record["id"], url_key(result["url"]))
                entry = pool.setdefault(key, {**result, "snippets": []})
                entry["snippets"].append(result.get("snippet") or "")
    return pool


def _page(url: str) -> dict:
    try:
        return {"url": url, "text": fetch_markdown(url)[:_PAGE_CHARS], "error": None}
    except Exception as e:  # noqa: BLE001 - an unfetchable page is graded from its snippets
        return {"url": url, "text": "", "error": f"{type(e).__name__}: {e}"}


def _grade(model: str, key: str, record: dict, entry: dict, page: dict) -> dict:
    if page["text"]:
        content, source = page["text"], "page"
    else:
        # Fall back to the longest provider snippet so no provider's wording is preferred.
        content, source = max(entry["snippets"], key=len)[:_PAGE_CHARS], "snippet"
    filters = ", ".join(f"site {d}" for d in record["domains"]) or "none"
    prompt = (
        f"Task given to the agent:\n{record['task'] or '(unknown)'}\n\n"
        f"Search query: {record['query']}\nSearch filters: {filters}\n\n"
        f"Page URL: {entry['url']}\nPage title: {entry.get('title') or ''}\n"
        f"Page content ({source}):\n{content or '(empty)'}"
    )
    body = {
        "model": model,
        # Room for models that think before answering; a 200-token cap left Haiku replies empty.
        "max_tokens": 1500,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _RUBRIC},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        data = post_json(_NANO_GPT, body, {"Authorization": f"Bearer {key}"})
        text = data["choices"][0]["message"]["content"]
        verdict = json.loads(re.search(r"\{.*\}", text, re.DOTALL)[0])
        grade, reason, error = int(verdict["grade"]), verdict.get("reason", ""), None
        if grade not in (0, 1, 2):
            raise ValueError(f"grade {grade}")
    except (ProviderError, KeyError, TypeError, ValueError) as e:
        grade, reason, error = None, "", f"{type(e).__name__}: {e}"
    return {
        "id": record["id"],
        "url_key": url_key(entry["url"]),
        "grade": grade,
        "reason": reason,
        "content": source,
        "model": model,
        "error": error,
    }


@cli.command()
@click.option(
    "--model",
    default=JUDGE_MODEL,
    show_default=True,
    help="NanoGPT model ID for the judge.",
)
@click.option("--workers", default=8, show_default=True)
@click.pass_obj
def judge(data_dir: Path, model: str, workers: int) -> None:
    """Paid: fetch and LLM-grade each query's pooled top results; resumes, retrying failures.

    The judge sees the caller's task, the query, and the page, never which provider found it.
    """
    records = {r["id"]: r for r in read_jsonl(data_dir / QUERIES)}
    pool = _pool(list(records.values()), latest_results(data_dir))

    pages = {url_key(p["url"]): p for p in read_jsonl(data_dir / PAGES)}
    missing = {k[1]: e["url"] for k, e in pool.items() if k[1] not in pages}
    with ThreadPoolExecutor(workers) as executor:
        for page in executor.map(_page, missing.values()):
            pages[url_key(page["url"])] = page
            append_jsonl(data_dir / PAGES, page)

    graded = {
        (j["id"], j["url_key"])
        for j in read_jsonl(data_dir / JUDGMENTS)
        if j["grade"] is not None and j["model"] == model
    }
    todo = [k for k in pool if k not in graded]
    api_key = read_secret("NANO_GPT_API_KEY", "NanoGPT API Key")
    failed = 0
    with ThreadPoolExecutor(workers) as executor:
        jobs = executor.map(
            lambda k: _grade(model, api_key, records[k[0]], pool[k], pages[k[1]]), todo
        )
        for verdict in jobs:
            append_jsonl(data_dir / JUDGMENTS, verdict)
            failed += verdict["grade"] is None
    unfetched = sum(1 for k in pool if pages[k[1]]["error"])
    click.echo(
        f"{len(pool)} pooled results ({len(missing)} pages fetched now, {unfetched} unfetchable "
        f"and graded from snippets); {len(todo)} graded now, {failed} failed"
    )
