"""Markdown rendering helpers."""

from __future__ import annotations

import re

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
    if len(msg) >= max_chars:
        return msg[:max_chars]
    return text[: max_chars - len(msg)] + msg


_MEGA_PARA_THRESHOLD = 1500  # chars; paragraphs above this get line-level matching


def _match_lines(para: str, matches: object, context: int) -> str:
    """Extract matching lines + context lines from a mega-paragraph."""
    lines = para.split("\n")
    keep: set[int] = set()
    for i, line in enumerate(lines):
        if matches(line):  # type: ignore[operator]
            lo = max(0, i - context)
            hi = min(len(lines), i + context + 1)
            keep.update(range(lo, hi))
    if not keep:
        return ""
    return "\n".join(lines[i] for i in sorted(keep))


def apply_find(text: str, pattern: str, context: int) -> str:
    """Return paragraphs matching pattern with context paragraphs around them.

    Pattern is tried as a case-insensitive regex. Falls back to literal
    substring matching when the pattern is not valid regex.
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

    try:
        compiled = re.compile(pattern, re.IGNORECASE)
        matches = compiled.search
    except re.error:
        needle = pattern.lower()

        def matches(para: str) -> bool:
            return needle in para.lower()

    keep: set[int] = set()
    mega_extracts: dict[int, str] = {}
    for i, para in enumerate(paragraphs):
        if len(para) > _MEGA_PARA_THRESHOLD:
            extracted = _match_lines(para, matches, context)
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
            f"[no paragraphs matched '{pattern}']\n\n"
            f"--- content preview (first 3 paragraphs) ---\n{preview}"
        )

    def _para_text(i: int) -> str:
        return mega_extracts.get(i, paragraphs[i])

    return "\n\n".join(_para_text(i) for i in sorted(keep))


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
