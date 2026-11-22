"""Sample past researcher searches into a replayable query set."""

from __future__ import annotations

import json
import random
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import click

from research.eval import cli
from research.eval._data import QUERIES, url_key, write_jsonl

# `opencode-sessions tools --full` prints each call as a header line ending in its JSON input,
# followed by its output when `--output` is set.
_CALL = re.compile(r"^(ses_\S+) \[(\d+)\] (\S+) \S+\s+(research_\w+) \[(\w+)\] (\{.*\})\s*$")
_DISCOVERED = re.compile(r"^\s*Discovered: (\S+)", re.MULTILINE)
_SUBAGENT_PREAMBLE = "You are a subagent spawned by another session."
_TASK_CHARS = 3000
# Searches restricted to only this domain go to the mslearn CLI, not the web search provider.
_MSLEARN = "learn.microsoft.com"


def _sessions(*args: str) -> str:
    result = subprocess.run(
        ["opencode-sessions", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise click.ClickException(f"opencode-sessions {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def _calls(text: str) -> list[dict]:
    """Split tool-call listings into header fields plus output text."""
    calls: list[dict] = []
    for line in text.splitlines():
        match = _CALL.match(line)
        if match:
            try:
                args = json.loads(match[6])
            except json.JSONDecodeError:
                calls.append({"skip": True, "output": []})
                continue
            calls.append(
                {
                    "session": match[1],
                    "seq": int(match[2]),
                    "date": match[3],
                    "status": match[5],
                    "args": args,
                    "output": [],
                }
            )
        elif calls:
            calls[-1]["output"].append(line)
    return [c for c in calls if not c.get("skip")]


def _task(session: str) -> str:
    """Return the caller's request that started a researcher session."""
    text = _sessions("show", session, "--range", "0:", "-n", "1", "--full")
    match = re.search(
        r"^--- \[\d+\] user [^\n]*\n(.*?)(?=^\[\d+ later messages|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if not match:
        return ""
    return match[1].replace(_SUBAGENT_PREAMBLE, "").strip()[:_TASK_CHARS]


def _replayable(call: dict) -> bool:
    output = "\n".join(call["output"])
    domains = call["args"].get("domains") or []
    return (
        call["status"] == "completed"
        and "RESERVED" not in output
        and bool(_DISCOVERED.search(output))
        and domains != [_MSLEARN]
    )


@cli.command()
@click.option("--since", default="2026-09-03", show_default=True, help="Oldest session date.")
@click.option("--size", default=120, show_default=True, help="Queries to sample.")
@click.option("--seed", default=1, show_default=True)
@click.pass_obj
def collect(data_dir: Path, since: str, size: int, seed: int) -> None:
    """Free: sample researcher searches with the pages the agent fetched from their results.

    Refuses to replace an existing query set. A query's gold URLs are results it returned that the same researcher session fetched
    afterwards. They favor whichever provider the researcher used when those sessions ran,
    since the agent could only fetch what that provider returned; the judge step offsets that.
    """
    # Run and judge data are keyed by query ID, so a new sample would silently reuse paid
    # results for different queries.
    if (data_dir / QUERIES).exists():
        raise click.ClickException(
            f"{data_dir / QUERIES} exists; collect a new sample into another --dir"
        )
    common = ["--agent", "researcher", "--since", since, "-n", "0", "--full"]
    searches = [
        c
        for c in _calls(_sessions("tools", "--name", "research_search", "--output", *common))
        if _replayable(c)
    ]
    fetched: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for call in _calls(_sessions("tools", "--name", "research_fetch", *common)):
        if url := call["args"].get("url"):
            fetched[call["session"]].append((call["seq"], url_key(url)))

    unique: dict[str, dict] = {}
    for call in searches:
        unique.setdefault(call["args"]["query"].strip().lower(), call)
    pool = sorted(unique.values(), key=lambda c: (c["session"], c["seq"]))

    # Stratify so domain-filtered and open searches keep their real proportions.
    rng = random.Random(seed)
    filtered = [c for c in pool if c["args"].get("domains")]
    open_ = [c for c in pool if not c["args"].get("domains")]
    take_filtered = round(size * len(filtered) / max(len(pool), 1))
    sample = rng.sample(filtered, min(take_filtered, len(filtered)))
    sample += rng.sample(open_, min(size - len(sample), len(open_)))

    tasks: dict[str, str] = {}
    records = []
    for i, call in enumerate(sorted(sample, key=lambda c: (c["date"], c["session"], c["seq"]))):
        session = call["session"]
        if session not in tasks:
            tasks[session] = _task(session)
        discovered = _DISCOVERED.findall("\n".join(call["output"]))
        later = {key for seq, key in fetched[session] if seq > call["seq"]}
        args = call["args"]
        records.append(
            {
                "id": f"q{i + 1:03d}",
                "session": session,
                "date": call["date"],
                "query": args["query"],
                "domains": args.get("domains") or [],
                "exclude_domains": args.get("exclude_domains") or [],
                "time_range": args.get("time_range"),
                "gold": [u for u in discovered if url_key(u) in later],
                "task": tasks[session],
            }
        )

    write_jsonl(data_dir / QUERIES, records)
    with_gold = sum(1 for r in records if r["gold"])
    click.echo(
        f"{len(records)} queries from {len(pool)} replayable searches "
        f"({len(filtered)} domain-filtered); {with_gold} have gold URLs. "
        f"Wrote {data_dir / QUERIES}"
    )
