"""Bot detection and comment body sanitization."""

from __future__ import annotations

import re


def is_bot(login: str, typename: str = "") -> bool:
    """Detect bot authors by GitHub convention.

    Checks both the '[bot]' suffix in login (REST API convention) and the
    GraphQL __typename field ('Bot' for app-installed bot accounts).
    """
    return "[bot]" in login or typename == "Bot"


# --- Block-level patterns (applied first, order matters) ---
_DETAILS_BLOCK = re.compile(r"<details\b[^>]*>.*?</details>", re.DOTALL | re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TABLE = re.compile(r"<table\b[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)
_MERMAID_BLOCK = re.compile(r"```mermaid\b.*?```", re.DOTALL)

# --- Inline patterns ---
_HTML_TAG = re.compile(r"<(?:br|hr)\s*/?>", re.IGNORECASE)
_HTML_PAIRED_TAG = re.compile(
    r"<(strong|b|em|i|code|a|span|td|tr|th|thead|tbody|ul|ol|li|p|h[1-6])\b[^>]*>"
    r"(.*?)"
    r"</\1>",
    re.DOTALL | re.IGNORECASE,
)
_HTML_LEFTOVER_TAG = re.compile(r"</?[a-z][a-z0-9]*\b[^>]*/?>", re.IGNORECASE)
_IMAGE_MARKDOWN = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_BADGE_LINK = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")

# --- Line-level patterns ---
_EMOJI_ONLY_LINE = re.compile(r"^\s*[\U0001f300-\U0001faff\u2600-\u27bf\s]+\s*$")
_DECORATIVE_SEPARATOR = re.compile(r"^\s*---+\s*$")
_MD_TABLE_SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
_MD_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")

# --- Whitespace cleanup ---
_CONSECUTIVE_BLANK = re.compile(r"\n{3,}")


def _strip_html_paired_tags(text: str) -> str:
    """Iteratively strip paired HTML tags, keeping inner text."""
    prev = None
    while prev != text:
        prev = text
        text = _HTML_PAIRED_TAG.sub(r"\2", text)
    return text


def sanitize_bot_body(body: str) -> str:
    """Strip boilerplate noise from a bot comment body.

    Removes: HTML details/table blocks, HTML comments, mermaid diagrams,
    markdown tables, inline HTML tags (keeping text), badge/image markdown,
    decorative lines. Collapses whitespace.
    """
    # Block removals
    text = _DETAILS_BLOCK.sub("", body)
    text = _HTML_COMMENT.sub("", text)
    text = _HTML_TABLE.sub("", text)
    text = _MERMAID_BLOCK.sub("", text)

    # Markdown table removal BEFORE inline HTML stripping. Table cells may
    # contain <br/> or <ul><li> tags; stripping those first would inject
    # newlines that break the |...|  row pattern.
    raw_lines = text.splitlines()
    table_lines: set[int] = set()
    for i, line in enumerate(raw_lines):
        if _MD_TABLE_SEPARATOR.match(line):
            table_lines.add(i)
            if i > 0 and _MD_TABLE_ROW.match(raw_lines[i - 1]):
                table_lines.add(i - 1)
            for j in range(i + 1, len(raw_lines)):
                if _MD_TABLE_ROW.match(raw_lines[j]):
                    table_lines.add(j)
                else:
                    break

    kept: list[str] = []
    for i, line in enumerate(raw_lines):
        if i in table_lines:
            continue
        if _EMOJI_ONLY_LINE.match(line):
            continue
        if _DECORATIVE_SEPARATOR.match(line):
            continue
        kept.append(line)
    text = "\n".join(kept)

    # Inline HTML: strip tags, keep text content
    text = _HTML_TAG.sub("\n", text)
    text = _strip_html_paired_tags(text)
    text = _HTML_LEFTOVER_TAG.sub("", text)

    # Strip badge links before images (badge links wrap images)
    text = _BADGE_LINK.sub("", text)
    text = _IMAGE_MARKDOWN.sub("", text)

    text = _CONSECUTIVE_BLANK.sub("\n\n", text)
    return text.strip()


def truncate_body(body: str, max_length: int) -> str:
    """Truncate body to max_length chars, appending a marker if truncated."""
    if max_length <= 0 or len(body) <= max_length:
        return body
    return f"{body[:max_length]} [truncated, {len(body)} chars]"
