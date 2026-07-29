"""Prose output formatting for LLM consumption."""

from __future__ import annotations

from typing import Any

from gh_review._sanitize import is_bot, sanitize_bot_body, truncate_body

PENDING_MARKER = " [pending, unsubmitted]"


def _author_info(author: dict[str, Any] | None) -> tuple[str, str]:
    """Extract (login, typename) from an author dict."""
    author = author or {}
    return author.get("login", "?"), author.get("__typename", "")


def _thread_status(thread: dict[str, Any]) -> str:
    flags = []
    if thread.get("isResolved"):
        flags.append("resolved")
    else:
        flags.append("unresolved")
    if thread.get("isOutdated"):
        flags.append("outdated")
    return ", ".join(flags)


def _line_label(thread: dict[str, Any]) -> str:
    start = thread.get("startLine")
    line = thread.get("line")
    if not line:
        return ""
    if start and start != line:
        return f"L{start}-{line}"
    return f"L{line}"


def _format_body(
    body: str,
    login: str,
    typename: str,
    max_body: int,
    no_bots: bool,
) -> str | None:
    """Process a comment body. Returns None if the comment should be dropped."""
    if not body:
        return ""
    bot = is_bot(login, typename)
    if bot and no_bots:
        return None
    if bot:
        body = sanitize_bot_body(body)
    return truncate_body(body, max_body)


def _comment_header(
    login: str,
    created: str,
    markers: str,
    db_id: int | None,
    indent: str,
    node_id: str | None = None,
) -> str:
    """Build a comment attribution header with optional databaseId and node id."""
    id_suffix = f" #{db_id}" if db_id else ""
    if node_id:
        id_suffix += f" {node_id}"
    return f"{indent}@{login} ({created}){markers}{id_suffix}:"


def _is_pending(comment: dict[str, Any]) -> bool:
    """Whether an inline comment belongs to an unsubmitted (pending) review."""
    return (comment.get("pullRequestReview") or {}).get("state") == "PENDING"


def format_review_threads(
    threads: list[dict[str, Any]],
    max_body: int,
    no_bots: bool,
) -> str:
    """Format review threads as prose output."""
    if not threads:
        return "no review threads"

    lines: list[str] = []
    for t in threads:
        status = _thread_status(t)
        path = t.get("path", "?")
        line_label = _line_label(t)
        location = f"{path} {line_label}".strip()

        lines.append(f"\n[{status}] {location}")

        comments = (t.get("comments") or {}).get("nodes", [])
        for c in comments:
            login, typename = _author_info(c.get("author"))
            raw_body = (c.get("body") or "").strip()
            created = (c.get("createdAt") or "")[:10]
            db_id = c.get("databaseId")

            processed = _format_body(
                raw_body,
                login,
                typename,
                max_body,
                no_bots,
            )
            if processed is None:
                continue

            bot = is_bot(login, typename)
            markers = " [bot, sanitized]" if bot else ""
            if _is_pending(c):
                markers += PENDING_MARKER
            header = _comment_header(login, created, markers, db_id, "  ", c.get("id"))

            if not processed:
                lines.append(header)
                continue

            body_lines = processed.splitlines()
            if len(body_lines) == 1:
                lines.append(f"{header} {body_lines[0]}")
            else:
                lines.append(header)
                for bl in body_lines:
                    lines.append(f"    {bl}")

    return "\n".join(lines)


def format_conversation_comments(
    comments: list[dict[str, Any]],
    max_body: int,
    no_bots: bool,
) -> str:
    """Format issue-level (conversation) comments as prose output."""
    if not comments:
        return "no conversation comments"

    lines: list[str] = []
    for c in comments:
        login, typename = _author_info(c.get("author"))
        raw_body = (c.get("body") or "").strip()
        created = (c.get("createdAt") or "")[:10]
        db_id = c.get("databaseId")

        processed = _format_body(
            raw_body,
            login,
            typename,
            max_body,
            no_bots,
        )
        if processed is None:
            continue

        bot = is_bot(login, typename)
        bot_marker = " [bot, sanitized]" if bot else ""
        header = _comment_header(login, created, bot_marker, db_id, "")

        if not processed:
            lines.append(header)
            continue

        body_lines = processed.splitlines()
        if len(body_lines) == 1:
            lines.append(f"{header} {body_lines[0]}")
        else:
            lines.append(header)
            for bl in body_lines:
                lines.append(f"  {bl}")

    return "\n".join(lines) if lines else "no conversation comments"


def format_review_bodies(
    reviews: list[dict[str, Any]],
    max_body: int,
    no_bots: bool,
) -> str:
    """Format top-level review body comments (the summary left on a review submission)."""
    if not reviews:
        return "no review comments"

    lines: list[str] = []
    for r in reviews:
        login, typename = _author_info(r.get("author"))
        raw_body = (r.get("body") or "").strip()
        created = (r.get("createdAt") or "")[:10]
        db_id = r.get("databaseId")
        state = (r.get("state") or "").lower()

        processed = _format_body(
            raw_body,
            login,
            typename,
            max_body,
            no_bots,
        )
        if processed is None:
            continue

        bot = is_bot(login, typename)
        bot_marker = " [bot, sanitized]" if bot else ""
        state_marker = f" [{state}]" if state else ""
        id_suffix = f" #{db_id}" if db_id else ""
        header = f"@{login} ({created}){bot_marker}{state_marker}{id_suffix}:"

        if not processed:
            lines.append(header)
            continue

        body_lines = processed.splitlines()
        if len(body_lines) == 1:
            lines.append(f"{header} {body_lines[0]}")
        else:
            lines.append(header)
            for bl in body_lines:
                lines.append(f"  {bl}")

    return "\n".join(lines) if lines else "no review comments"


def format_pending_reviews(reviews: list[dict[str, Any]], max_body: int) -> str:
    """Format pending review entries with their unsubmitted body and inline comments."""
    if not reviews:
        return ""
    lines = ["=== PENDING REVIEWS (not visible to others until submitted) ==="]
    for r in reviews:
        author = (r.get("author") or {}).get("login", "?")
        comments = (r.get("comments") or {}).get("nodes", [])
        count = len(comments)
        noun = "comment" if count == 1 else "comments"
        lines.append(f"{r['id']} @{author} ({count} inline {noun})")

        body = (r.get("body") or "").strip()
        if body:
            lines.append("  body:")
            for bl in truncate_body(body, max_body).splitlines():
                lines.append(f"    {bl}")

        for c in comments:
            location = f"{c.get('path', '?')} {_line_label(c)}".strip()
            id_suffix = f" #{c['databaseId']}" if c.get("databaseId") else ""
            if c.get("id"):
                id_suffix += f" {c['id']}"
            header = f"  {location}{id_suffix}:"
            body_lines = truncate_body((c.get("body") or "").strip(), max_body).splitlines()
            if len(body_lines) == 1:
                lines.append(f"{header} {body_lines[0]}")
                continue
            lines.append(header)
            for bl in body_lines:
                lines.append(f"    {bl}")
    return "\n".join(lines)
