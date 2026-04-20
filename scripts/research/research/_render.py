"""Markdown rendering helpers."""

from __future__ import annotations

import re
import sys


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


def truncate_output(text: str, max_chars: int, default_max: int = 20000) -> str:
    """Truncate text with helpful message.

    max_chars <= 0 disables truncation.
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    msg = (
        f'\n\n[truncated at {max_chars} chars; prefer --find "pattern" '
        "to target specific sections; --max-chars 0 disables truncation]"
    )
    return text[:max_chars] + msg


def apply_find(text: str, pattern: str, context: int) -> str:
    """Return paragraphs matching pattern with context paragraphs around them."""
    paragraphs = text.split("\n\n")
    needle = pattern.lower()
    keep: set[int] = set()
    for i, para in enumerate(paragraphs):
        if needle in para.lower():
            lo = max(0, i - context)
            hi = min(len(paragraphs), i + context + 1)
            keep.update(range(lo, hi))
    if not keep:
        return f"[no paragraphs matched '{pattern}']"
    return "\n\n".join(paragraphs[i] for i in sorted(keep))


def reroute_message(url: str, new_command: str, reason: str) -> None:
    """Print a concise reroute banner to stderr."""
    print(
        f"[reroute: {url} -> {new_command}; reason: {reason}; rerouted output follows]",
        file=sys.stderr,
        flush=True,
    )


def format_error(action: str, reason: str) -> str:
    """Return a formatted error message."""
    return f"error: {action} failed: {reason}"


def format_issue_body(number: int, title: str, state: str, created: str, body: str) -> str:
    """Format an issue/PR as markdown."""
    lines = [f"## #{number}: {title}", "", f"- **State:** {state}", f"- **Created:** {created}"]
    if body:
        lines.extend(["", body])
    return "\n".join(lines)


def format_comment(author: str, date: str, body: str) -> str:
    """Format a comment as markdown."""
    return f"**@{author} ({date}):**\n\n{body}"


def format_list_item(
    number: int, state: str, date: str, title: str, max_title_len: int = 80
) -> str:
    """Format a list entry as a bullet item."""
    short_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
    return f"- #{number} ({state}) {date[:10]} {short_title}"


def format_commit_item(sha: str, date: str, message: str, max_msg_len: int = 100) -> str:
    """Format a commit list entry as a bullet item."""
    short_msg = message[:max_msg_len] + "..." if len(message) > max_msg_len else message
    short_sha = sha[:8] if len(sha) > 8 else sha
    return f"- {short_sha} ({date[:10]}) {short_msg}"


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
