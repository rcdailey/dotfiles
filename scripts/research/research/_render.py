"""Markdown rendering helpers."""

from __future__ import annotations

import re
from collections.abc import Callable

import click


def section_heading(title: str) -> str:
    """Return a markdown section heading."""
    return f"\n## {title}\n"


def sub_heading(title: str) -> str:
    """Return a markdown subheading."""
    return f"\n### {title}\n"


def kv_line(key: str, value: str) -> str:
    """Return a key: value line."""
    return f"- **{key}:** {value}"


def bullet_item(text: str) -> str:
    """Return a bullet list item."""
    return f"- {text}"


def fenced_code(content: str, language: str = "") -> str:
    """Return content wrapped in a fenced code block."""
    return f"\n```{language}\n{content}\n```\n"


DEFAULT_MAX_CHARS = 12000
DEFAULT_SCOUT_MAX_CHARS = DEFAULT_MAX_CHARS


def truncate_output(text: str, max_chars: int, hint: str | None = None) -> str:
    """Truncate text with helpful message.

    max_chars <= 0 disables truncation.
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    guidance = hint or 'prefer --find "pattern"; --max-chars 0 disables truncation'
    msg = f"\n\n[truncated at {max_chars} chars; {guidance}]"
    if len(msg) >= max_chars or len(msg) > max_chars // 3:
        msg = "\n\n[truncated]"
        if len(msg) >= max_chars:
            return text[:max_chars]
    return text[: max_chars - len(msg)] + msg


_MEGA_PARA_THRESHOLD = 1500  # chars; paragraphs above this get line-level matching


def _add_line_context(
    keep: set[int],
    first: int,
    last: int,
    line_count: int,
    context: int,
) -> None:
    """Add a matching line range and its context to the retained indexes."""
    keep.update(range(max(0, first - context), min(line_count, last + context + 1)))


def _match_lines(
    para: str,
    matches: Callable[[str], bool],
    compiled: re.Pattern[str] | None,
    normalized_needle: str,
    context: int,
) -> str:
    """Extract matching lines + context lines from a mega-paragraph."""
    lines = para.split("\n")
    keep: set[int] = set()
    for i, line in enumerate(lines):
        if matches(line):
            _add_line_context(keep, i, i, len(lines), context)

    if compiled is not None:
        for match in compiled.finditer(para):
            first = para.count("\n", 0, match.start())
            last_char = max(match.start(), match.end() - 1)
            last = para.count("\n", 0, last_char)
            _add_line_context(keep, first, last, len(lines), context)

    normalized_parts: list[str] = []
    line_spans: list[tuple[int, int, int]] = []
    cursor = 0
    for line_index, line in enumerate(lines):
        normalized_line = " ".join(line.casefold().split())
        if not normalized_line:
            continue
        if normalized_parts:
            cursor += 1
        start = cursor
        normalized_parts.append(normalized_line)
        cursor += len(normalized_line)
        line_spans.append((start, cursor, line_index))

    normalized_para = " ".join(normalized_parts)
    search_from = 0
    while normalized_needle:
        match_start = normalized_para.find(normalized_needle, search_from)
        if match_start < 0:
            break
        match_end = match_start + len(normalized_needle)
        matched_lines = [
            line_index
            for start, end, line_index in line_spans
            if end > match_start and start < match_end
        ]
        if matched_lines:
            _add_line_context(
                keep,
                matched_lines[0],
                matched_lines[-1],
                len(lines),
                context,
            )
        search_from = match_start + 1

    if not keep:
        return ""
    return "\n".join(lines[i] for i in sorted(keep))


def apply_find(text: str, pattern: str, context: int) -> tuple[str, bool]:
    """Return rendered paragraphs and whether the pattern matched.

    Pattern is tried as a case-insensitive regex. Matching also tolerates
    whitespace changes introduced by content extraction.
    Mega-paragraphs (> _MEGA_PARA_THRESHOLD chars) are matched at line level
    to avoid returning thousands of unrelated characters.
    """
    if r"\|" in pattern:
        fixed = pattern.replace(r"\|", "|")
        click.echo(
            "[hint: converted \\| to | for regex alternation; use | directly next time]",
            err=True,
        )
        pattern = fixed

    paragraphs = text.split("\n\n")

    normalized_needle = " ".join(pattern.casefold().split())

    try:
        compiled = re.compile(pattern, re.IGNORECASE)

        def matches(value: str) -> bool:
            normalized_value = " ".join(value.casefold().split())
            return bool(compiled.search(value)) or normalized_needle in normalized_value

    except re.error:
        compiled = None

        def matches(value: str) -> bool:
            normalized_value = " ".join(value.casefold().split())
            return normalized_needle in normalized_value

    keep: set[int] = set()
    mega_extracts: dict[int, str] = {}
    for i, para in enumerate(paragraphs):
        if len(para) > _MEGA_PARA_THRESHOLD:
            extracted = _match_lines(para, matches, compiled, normalized_needle, context)
            if extracted:
                mega_extracts[i] = extracted
                keep.add(i)
        elif matches(para):
            lo = max(0, i - context)
            hi = min(len(paragraphs), i + context + 1)
            keep.update(range(lo, hi))
    if not keep:
        preview = "\n\n".join(paragraphs[:3])
        if len(preview) > 500:
            preview = preview[:500] + "..."
        return (
            f"error: no paragraphs matched '{pattern}'\n\n"
            f"--- content preview (first 3 paragraphs) ---\n{preview}"
        ), False

    def _para_text(i: int) -> str:
        return mega_extracts.get(i, paragraphs[i])

    return "\n\n".join(_para_text(i) for i in sorted(keep)), True


def reroute_message(url: str, new_command: str, reason: str) -> None:
    """Print a concise reroute banner to stderr."""
    click.echo(
        f"[reroute: {url} -> {new_command}; reason: {reason}; rerouted output follows]",
        err=True,
    )


def format_error(action: str, reason: str) -> str:
    """Return a formatted error message."""
    return f"error: {action} failed: {reason}"


def format_issue_body(
    number: int,
    title: str,
    state: str,
    created: str,
    body: str,
    source_url: str | None = None,
) -> str:
    """Format an issue/PR as markdown."""
    lines = [f"## #{number}: {title}", "", f"- **State:** {state}", f"- **Created:** {created}"]
    if source_url:
        lines.append(f"- **Source:** {source_url}")
    if body:
        lines.extend(["", body])
    return "\n".join(lines)


def format_comment(author: str, date: str, body: str) -> str:
    """Format a comment as markdown."""
    return f"**@{author} ({date}):**\n\n{body}"


def format_list_item(
    number: int,
    state: str,
    date: str,
    title: str,
    max_title_len: int = 80,
    source_url: str | None = None,
) -> str:
    """Format a list entry as a bullet item."""
    short_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
    item = f"- #{number} ({state}) {date[:10]} {short_title}"
    return f"{item}\n  Source: {source_url}" if source_url else item


def format_commit_item(
    sha: str,
    date: str,
    message: str,
    max_msg_len: int = 100,
    source_url: str | None = None,
) -> str:
    """Format a commit list entry as a bullet item."""
    short_msg = message[:max_msg_len] + "..." if len(message) > max_msg_len else message
    short_sha = sha[:8] if len(sha) > 8 else sha
    item = f"- {short_sha} ({date[:10]}) {short_msg}"
    return f"{item}\n  Source: {source_url}" if source_url else item


def strip_github_host(url: str) -> str:
    """Strip github.com prefix from URL, return path."""
    match = re.match(r"^https?://(?:www\.)?github\.com/(.+)", url, re.IGNORECASE)
    if match:
        return match.group(1).split("?")[0].split("#")[0].strip("/")
    return ""


def is_github_url(url: str) -> bool:
    """Check if URL is a github.com URL."""
    return bool(re.match(r"^https?://(?:www\.)?github\.com/", url, re.IGNORECASE))


def is_pdf_url(url: str) -> bool:
    """Check if URL points to a PDF."""
    return bool(re.search(r"\.pdf(?:$|[?#])", url, re.IGNORECASE))
