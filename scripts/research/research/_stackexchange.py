"""Stack Exchange question retrieval through the public API.

Stack Overflow and its sibling sites answer direct page fetches with HTTP 403. The API serves the
same questions and answers without a key, within a quota of 300 requests per day per IP address.
"""

from __future__ import annotations

import html
import json
import re
import time
from urllib.parse import urlparse

from research._fetch import FetchError, fetch_response

_API = "https://api.stackexchange.com/2.3"
# Created via /filters/create; filters are permanent. Default fields plus question.answers,
# body_markdown for questions and answers, accepted_answer_id, closed_reason/closed_date, and
# edit dates. body_markdown is the author's source, so no HTML conversion is needed.
_FILTER = "!)RL-JogHwoZuazwxM.funK5M"
_SITE_HOSTS = (
    "stackoverflow.com",
    "superuser.com",
    "serverfault.com",
    "askubuntu.com",
    "mathoverflow.net",
    "stackapps.com",
)
_POST_PATH_RE = re.compile(r"^/(questions|q|a)/(\d+)(?:/[^/]+/(\d+))?")
# The API sets `backoff` when a client must pause before calling the same method again.
_MAX_BACKOFF = 30.0


def stackexchange_post(url: str) -> tuple[str, str, int] | None:
    """Return (site, kind, id) for a question or answer URL; kind is "question" or "answer".

    The site is the URL's host, which the API accepts as its `site` parameter, including
    `meta.` and language subdomains.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").removeprefix("www.")
    is_site = host.endswith(".stackexchange.com") and host != "api.stackexchange.com"
    if not (is_site or any(host == h or host.endswith(f".{h}") for h in _SITE_HOSTS)):
        return None
    match = _POST_PATH_RE.match(parsed.path)
    if not match:
        return None
    prefix, post_id, answer_id = match.groups()
    if answer_id:
        return host, "answer", int(answer_id)
    return host, "answer" if prefix == "a" else "question", int(post_id)


def fetch_post(site: str, kind: str, post_id: int) -> str:
    """Render the question containing the post, with every answer, as markdown.

    A linked answer is listed first; the rest follow with the accepted answer first, then by
    score. Raises FetchError with status 404 when the post does not exist or was deleted.
    """
    linked_answer = None
    question_id = post_id
    if kind == "answer":
        answers = _api_items(f"/answers/{post_id}", site, "default")
        if not answers:
            raise FetchError("answer not found or deleted", 404)
        linked_answer = post_id
        question_id = answers[0]["question_id"]
    questions = _api_items(f"/questions/{question_id}", site, _FILTER)
    if not questions:
        raise FetchError("question not found or deleted", 404)
    return _render_question(questions[0], linked_answer)


def _api_items(path: str, site: str, api_filter: str) -> list[dict]:
    try:
        response = fetch_response(f"{_API}{path}?site={site}&filter={api_filter}")
    except FetchError as e:
        # The API reports bad parameters and quota exhaustion as HTTP 400, and missing posts as
        # empty items; drop the status so a 400 is not reported as a missing page.
        raise FetchError(f"Stack Exchange API request failed: {e}") from e
    try:
        payload = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise FetchError(f"Stack Exchange API returned invalid JSON: {e}") from e
    if "error_id" in payload:
        raise FetchError(
            f"Stack Exchange API {payload.get('error_name')}: {payload.get('error_message')}"
        )
    backoff = payload.get("backoff")
    if backoff:
        time.sleep(min(float(backoff), _MAX_BACKOFF))
    return payload.get("items") or []


def _render_question(question: dict, linked_answer: int | None) -> str:
    meta = [
        _byline(question),
        f"{question.get('view_count', '?')} views",
        f"{question.get('answer_count', 0)} answers",
        f"tags: {', '.join(question.get('tags') or [])}",
    ]
    if question.get("closed_date"):
        meta.append(f"closed {_utc_date(question['closed_date'])}: {question.get('closed_reason')}")
    parts = [
        f"# {html.unescape(question.get('title', ''))}",
        f"Source: {question.get('link', '')}",
        " | ".join(meta),
        _body_markdown(question),
    ]
    accepted = question.get("accepted_answer_id")
    answers = sorted(
        question.get("answers") or [],
        key=lambda a: (
            a["answer_id"] != linked_answer,
            a["answer_id"] != accepted,
            -a.get("score", 0),
        ),
    )
    for answer in answers:
        labels = [
            label
            for label, applies in (
                ("linked", answer["answer_id"] == linked_answer),
                ("accepted", answer["answer_id"] == accepted),
            )
            if applies
        ]
        suffix = f" ({', '.join(labels)})" if labels else ""
        link = f"{question.get('link', '')}/{answer['answer_id']}#{answer['answer_id']}"
        parts.append(
            f"---\n\n## Answer {answer['answer_id']}{suffix}\n\n"
            f"{_byline(answer)} | {link}\n\n{_body_markdown(answer)}"
        )
    if not answers:
        parts.append("---\n\nNo answers.")
    return "\n\n".join(parts)


def _byline(post: dict) -> str:
    owner = html.unescape((post.get("owner") or {}).get("display_name", "[deleted]"))
    edited = f", edited {_utc_date(post['last_edit_date'])}" if post.get("last_edit_date") else ""
    created = _utc_date(post.get("creation_date"))
    return f"{owner} | score {post.get('score', '?')} | {created}{edited}"


def _body_markdown(post: dict) -> str:
    """Return the post's markdown source; the API HTML-escapes it (e.g. &quot;)."""
    return html.unescape(post.get("body_markdown", "")).strip()


def _utc_date(timestamp: object) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(float(timestamp or 0)))
