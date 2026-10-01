"""Block and inline rules that Rewrap lacks: directive fences, HTML tag lines, and MDX.

These keep non-prose lines from joining with prose. Each rule that "interrupts" a paragraph
also ends any paragraph directly above it, so blank lines around such lines are optional.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from mdwrap._blocks import NO_WRAP, Line, Res, TryParser, finished, md_marker, pending
from mdwrap._markdown import until_match

_BLANK = re.compile(r"^\s*$")
_DIRECTIVE_FENCE = md_marker(r":{3,}(?:[A-Za-z][\w-]*)?(?:\[.*\])?(?:\{.*\})?\s*$")
_INDENT = re.compile(r"^ {0,3}")
_HTML_TAG_NAME = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
_JSX_TAG_NAME = re.compile(r"[A-Za-z_$][\w$.:-]*")
# CommonMark HTML block types 1 and 4 cover these; their blocks may hold blank lines.
_RAW_HTML_TAGS = frozenset({"script", "style", "pre", "textarea"})


def directive_fence(line: Line) -> Res | None:
    return finished(line, NO_WRAP) if _DIRECTIVE_FENCE.search(line.content) else None


def _skip_string(text: str, i: int) -> int | None:
    """Return the index after the quoted string starting at `i`, or None if unterminated."""
    end = text.find(text[i], i + 1)
    return None if end < 0 else end + 1


def _skip_braces(text: str, i: int) -> int | None:
    """Return the index after the balanced `{...}` starting at `i`, or None if unbalanced."""
    depth = 0
    while i < len(text):
        ch = text[i]
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                return None
            i = end + 2
            continue
        if text.startswith("//", i):
            end = text.find("\n", i + 2)
            if end < 0:
                return None
            i = end + 1
            continue
        if ch in "\"'`":
            nxt = _skip_string(text, i)
            if nxt is None:
                return None
            i = nxt
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _skip_tag(text: str, i: int, *, jsx: bool) -> int | None:
    """Return the index after the complete tag starting at `text[i] == "<"`, or None."""
    j = i + 1
    if j < len(text) and text[j] == "/":
        j += 1
    name = (_JSX_TAG_NAME if jsx else _HTML_TAG_NAME).match(text, j)
    if name:
        j = name.end()
    elif not (jsx and j < len(text) and text[j] == ">"):  # JSX fragment: <> or </>
        return None
    if j < len(text) and not (text[j].isspace() or text[j] in "/>"):
        return None
    while j < len(text):
        ch = text[j]
        if ch == ">":
            return j + 1
        if ch in "\"'":
            nxt = _skip_string(text, j)
        elif jsx and ch == "{":
            nxt = _skip_braces(text, j)
        elif ch == "<":
            return None
        else:
            nxt = j + 1
        if nxt is None:
            return None
        j = nxt
    return None


def _first_tag_name(text: str) -> str:
    m = _HTML_TAG_NAME.match(text, 2 if text.startswith("</") else 1)
    return m[0].lower() if m else ""


def _tags_only(text: str, *, jsx: bool) -> bool:
    """Whether `text` holds one or more complete tags and nothing else but whitespace."""
    i = 0
    found = False
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text[i] != "<":
            return False
        nxt = _skip_tag(text, i, jsx=jsx)
        if nxt is None:
            return False
        i, found = nxt, True
    return found


def _html_block_from(line: Line) -> Res:
    return until_match(_BLANK, line, len(line.content))


def html_tag_line(line: Line) -> Res | None:
    text = line.content[_INDENT.match(line.content).end() :]
    if not text.startswith("<") or _first_tag_name(text) in _RAW_HTML_TAGS:
        return None
    return _html_block_from(line) if _tags_only(text, jsx=False) else None


def jsx_tag_line(line: Line) -> Res | None:
    """MDX flow JSX: tag-only lines, including an opening tag whose attributes span lines."""
    text = line.content[_INDENT.match(line.content).end() :]
    if not text.startswith("<"):
        return None
    if _tags_only(text, jsx=True):
        return _html_block_from(line)
    if _opens_multiline_tag(text):
        return pending(line, NO_WRAP, _continue_tag(text))
    return None


def _opens_multiline_tag(text: str) -> bool:
    """Whether `text` is the start of an opening tag that continues on the next line."""
    if not re.match(r"<[A-Za-z_$]", text) or _skip_tag(text, 0, jsx=True) is not None:
        return False
    return _skip_tag(text + "\n>", 0, jsx=True) is not None


def _continue_tag(acc: str) -> Callable[[Line], Res]:
    def parse(line: Line) -> Res:
        # A tag left open at a blank line is malformed; end the block so the rest still wraps.
        if line.is_blank():
            return finished(line, NO_WRAP)
        text = acc + "\n" + line.content
        if _skip_tag(text, 0, jsx=True) is not None:
            return _html_block_from(line)
        return pending(line, NO_WRAP, _continue_tag(text))

    return parse


def _expression_line(text: str) -> bool:
    end = _skip_braces(text, 0)
    return end is not None and not text[end:].strip()


def jsx_expression_line(line: Line) -> Res | None:
    """MDX flow expression: a line holding only `{...}`, possibly spanning lines."""
    text = line.content[_INDENT.match(line.content).end() :]
    if not text.startswith("{"):
        return None
    if _expression_line(text):
        return finished(line, NO_WRAP)
    if _skip_braces(text, 0) is None:
        return pending(line, NO_WRAP, _continue_expression(text))
    return None


def _continue_expression(acc: str) -> Callable[[Line], Res]:
    def parse(line: Line) -> Res:
        text = acc + "\n" + line.content
        if _skip_braces(text, 0) is not None:
            return finished(line, NO_WRAP)
        return pending(line, NO_WRAP, _continue_expression(text))

    return parse


_ESM = re.compile(r"^(import|export)\s")


def esm(line: Line) -> Res | None:
    """MDX ESM block at document level, through the next blank line."""
    if line.prefix or not _ESM.search(line.content):
        return None
    return _html_block_from(line)


def mdx_unbreakable(text: str) -> frozenset[int]:
    """Positions inside inline JSX tags and `{...}` expressions, where breaks are forbidden."""
    protected: set[int] = set()
    i = 0
    while i < len(text):
        ch = text[i]
        end = None
        if ch == "<":
            end = _skip_tag(text, i, jsx=True)
        elif ch == "{":
            end = _skip_braces(text, i)
        if end is None:
            i += 1
            continue
        protected.update(range(i + 1, end))
        i = end
    return frozenset(protected)


MARKDOWN_INTERRUPTERS: list[TryParser] = [directive_fence, html_tag_line]
MDX_INTERRUPTERS: list[TryParser] = [directive_fence, jsx_tag_line, jsx_expression_line]
MDX_BLOCK_STARTS: list[TryParser] = [esm]
