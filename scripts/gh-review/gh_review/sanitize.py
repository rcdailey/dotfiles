"""Bot detection and comment body sanitization."""

from __future__ import annotations

import re


def is_bot(login: str, typename: str = "") -> bool:
    """Detect bot authors by GitHub convention.

    Checks both the '[bot]' suffix in login (REST API convention) and the
    GraphQL __typename field ('Bot' for app-installed bot accounts).
    """
    return "[bot]" in login or typename == "Bot"


# Patterns applied to bot comment bodies (order matters).
_DETAILS_BLOCK = re.compile(r"<details\b[^>]*>.*?</details>", re.DOTALL | re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_EMOJI_ONLY_LINE = re.compile(r"^\s*[\U0001f300-\U0001faff\u2600-\u27bf\s]+\s*$")
_DECORATIVE_SEPARATOR = re.compile(r"^\s*---+\s*$")
_CONSECUTIVE_BLANK = re.compile(r"\n{3,}")


def sanitize_bot_body(body: str) -> str:
    """Strip boilerplate noise from a bot comment body.

    Removes HTML details blocks (suggestions, learnings, config), HTML comments
    (fingerprinting, metadata), purely decorative lines, and collapses whitespace.
    These are structural patterns shared across review bots, not bot-specific rules.
    """
    text = _DETAILS_BLOCK.sub("", body)
    text = _HTML_COMMENT.sub("", text)

    lines = []
    for line in text.splitlines():
        if _EMOJI_ONLY_LINE.match(line):
            continue
        if _DECORATIVE_SEPARATOR.match(line):
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = _CONSECUTIVE_BLANK.sub("\n\n", text)
    return text.strip()


def truncate_body(body: str, max_length: int) -> str:
    """Truncate body to max_length chars, appending a marker if truncated."""
    if max_length <= 0 or len(body) <= max_length:
        return body
    return f"{body[:max_length]} [truncated, {len(body)} chars]"
