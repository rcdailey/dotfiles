"""Bot detection and comment body sanitization."""

from __future__ import annotations

import re
from collections.abc import Callable

from gh_review import _coderabbit

# Decides whether a collapsed <details> block survives sanitizing, given its summary text and
# whether an enclosing block was kept. Bots without a policy lose every <details> block.
type DetailsPolicy = Callable[[str, bool], bool]

# Keyed by login without the REST "[bot]" suffix. Add a module per bot whose review bodies
# collapse actionable content.
_DETAILS_POLICIES: dict[str, DetailsPolicy] = {_coderabbit.LOGIN: _coderabbit.keeps_details}


def is_bot(login: str, typename: str = "") -> bool:
    """Detect bot authors by GitHub convention.

    Checks both the '[bot]' suffix in login (REST API convention) and the
    GraphQL __typename field ('Bot' for app-installed bot accounts).
    """
    return "[bot]" in login or typename == "Bot"


# --- Block-level patterns (applied first, order matters) ---
_DETAILS_TAG = re.compile(r"<details\b[^>]*>|</details\s*>", re.IGNORECASE)
_SUMMARY = re.compile(r"\s*<summary\b[^>]*>(.*?)</summary\s*>", re.DOTALL | re.IGNORECASE)
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


def _drop_all_details(summary: str, in_kept: bool) -> bool:
    return False


def _filter_details(text: str, keeps: DetailsPolicy, in_kept: bool = False) -> str:
    """Drop collapsed <details> blocks except those the author's policy keeps.

    Kept blocks render as their summary line followed by their filtered content, so the policy
    still decides each nested block.
    """
    out: list[str] = []
    pos = 0
    while (start := _DETAILS_TAG.search(text, pos)) is not None:
        out.append(text[pos : start.start()])
        if start.group().startswith("</"):
            pos = start.end()
            continue
        depth = 1
        end = start
        while depth and (end := _DETAILS_TAG.search(text, end.end())) is not None:
            depth += -1 if end.group().startswith("</") else 1
        if end is None:
            return "".join(out) + text[start.start() :]
        inner = text[start.end() : end.start()]
        pos = end.end()
        summary_match = _SUMMARY.match(inner)
        summary = summary_match.group(1).strip() if summary_match else ""
        if not keeps(summary, in_kept):
            continue
        content = inner[summary_match.end() :] if summary_match else inner
        out.append(f"\n{summary}\n{_filter_details(content, keeps, in_kept=True)}\n")
    out.append(text[pos:])
    return "".join(out)


def sanitize_bot_body(body: str, login: str = "") -> str:
    """Strip boilerplate noise from a bot comment body.

    Removes: HTML details blocks (unless the bot's policy in _DETAILS_POLICIES
    keeps them), HTML comments and tables, mermaid diagrams, markdown tables,
    inline HTML tags (keeping text), badge/image markdown, decorative lines.
    Collapses whitespace.
    """
    keeps = _DETAILS_POLICIES.get(login.removesuffix("[bot]"), _drop_all_details)
    # Block removals
    text = _filter_details(body, keeps)
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
