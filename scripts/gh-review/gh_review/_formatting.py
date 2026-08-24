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


def _comment_lines(
    comment: dict[str, Any],
    *,
    indent: str,
    max_body: int,
    no_bots: bool,
    node_id: bool = True,
    extra_markers: str = "",
) -> list[str] | None:
    """Render one comment as attribution header plus indented body, or None if dropped."""
    login, typename = _author_info(comment.get("author"))
    processed = _format_body(
        (comment.get("body") or "").strip(),
        login,
        typename,
        max_body,
        no_bots,
    )
    if processed is None:
        return None

    markers = (" [bot, sanitized]" if is_bot(login, typename) else "") + extra_markers
    header = _comment_header(
        login,
        (comment.get("createdAt") or "")[:10],
        markers,
        comment.get("databaseId"),
        indent,
        comment.get("id") if node_id else None,
    )
    if not processed:
        return [header]

    body_lines = processed.splitlines()
    if len(body_lines) == 1:
        return [f"{header} {body_lines[0]}"]
    return [header, *(f"{indent}  {bl}" for bl in body_lines)]


def _thread_lines(thread: dict[str, Any], max_body: int, no_bots: bool) -> list[str]:
    """Render one review thread: location header plus its comments."""
    location = f"{thread.get('path', '?')} {_line_label(thread)}".strip()
    lines: list[str] = []
    for c in (thread.get("comments") or {}).get("nodes", []):
        extra = PENDING_MARKER if _is_pending(c) else ""
        rendered = _comment_lines(
            c,
            indent="    ",
            max_body=max_body,
            no_bots=no_bots,
            extra_markers=extra,
        )
        if rendered is not None:
            lines.extend(rendered)
    if not lines:
        return []
    return [f"  [{_thread_status(thread)}] {location}", *lines]


def format_reviews(
    groups: list[tuple[dict[str, Any] | None, list[dict[str, Any]]]],
    max_body: int,
    no_bots: bool,
) -> str:
    """Format reviews with their inline threads nested under each review."""
    blocks: list[str] = []
    for review, threads in groups:
        lines: list[str] = []
        if review is not None:
            if not (review.get("body") or "").strip() and not threads:
                continue
            state = (review.get("state") or "").lower()
            rendered = _comment_lines(
                review,
                indent="",
                max_body=max_body,
                no_bots=no_bots,
                node_id=False,
                extra_markers=f" [{state}]" if state else "",
            )
            if rendered is None and not threads:
                continue
            if rendered is not None:
                lines.extend(rendered)

        for t in threads:
            thread_lines = _thread_lines(t, max_body, no_bots)
            if not thread_lines:
                continue
            if lines:
                lines.append("")
            lines.extend(thread_lines)

        if lines:
            blocks.append("\n".join(lines))

    return "\n\n".join(blocks) if blocks else "no reviews"


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
        rendered = _comment_lines(
            c,
            indent="",
            max_body=max_body,
            no_bots=no_bots,
            node_id=False,
        )
        if rendered is not None:
            lines.extend(rendered)

    return "\n".join(lines) if lines else "no conversation comments"


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
