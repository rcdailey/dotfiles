"""Inline Markdown spans that a line break must not split.

Covered: code spans, inline and reference links and images (with a directly following
`{...}` attribute list), and the label and destination of a link reference definition at the
start of a paragraph. Autolinks need no rule because they cannot contain whitespace.
"""

from __future__ import annotations

import re

_LINK_REF_DEF = re.compile(r"\[[^\]]+\]:[ \t]*(?:<[^<>\n]*>|\S+)")
_ATTR_LIST = re.compile(r"\{[^{}\n]*\}")


def _backtick_run_end(text: str, i: int) -> int:
    while i < len(text) and text[i] == "`":
        i += 1
    return i


def _code_span(text: str, i: int) -> tuple[int, bool]:
    """Return where scanning resumes after the backtick run at `i`, and whether it opened a
    code span (closed by the next run of the same length)."""
    run_end = _backtick_run_end(text, i)
    j = run_end
    while (j := text.find("`", j)) >= 0:
        k = _backtick_run_end(text, j)
        if k - j == run_end - i:
            return k, True
        j = k
    return run_end, False


def _skip_balanced(text: str, i: int, open_ch: str, close_ch: str) -> int | None:
    """Return the index after the bracket group opening at `i`, or None if unbalanced."""
    depth = 0
    j = i
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "`":
            j = _code_span(text, j)[0]
            continue
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return None


def _skip_link(text: str, i: int) -> int | None:
    """Return the end of the link or image starting at `i`, or None if there is none."""
    start = i + 1 if text[i] == "!" else i
    label_end = _skip_balanced(text, start, "[", "]")
    if label_end is None or label_end >= len(text):
        return None
    if text[label_end] == "(":
        end = _skip_balanced(text, label_end, "(", ")")
    elif text[label_end] == "[":
        end = _skip_balanced(text, label_end, "[", "]")
    else:
        return None
    if end is None:
        return None
    attrs = _ATTR_LIST.match(text, end)
    return attrs.end() if attrs else end


def markdown_unbreakable(text: str) -> frozenset[int]:
    """Positions inside unbreakable spans of a paragraph's joined text."""
    protected: set[int] = set()

    def protect(start: int, end: int) -> None:
        protected.update(range(start + 1, end))

    if definition := _LINK_REF_DEF.match(text):
        protect(0, definition.end())
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "`":
            end, is_span = _code_span(text, i)
            if is_span:
                protect(i, end)
            i = end
            continue
        if ch == "[" or (ch == "!" and text.startswith("[", i + 1)):
            end = _skip_link(text, i)
            if end is not None:
                protect(i, end)
                i = end
                continue
        i += 1
    return frozenset(protected)
