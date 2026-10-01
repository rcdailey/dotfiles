"""Markdown block grammar for the line parser in `_blocks`.

Behavior baseline: Rewrap's Markdown parser (dnut/Rewrap `core/Parsers_Markdown.fs`).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from mdwrap._blocks import (
    NO_WRAP,
    WRAP,
    FirstLineParser,
    Kind,
    Line,
    Prev,
    Res,
    TryParser,
    container,
    finished,
    md_marker,
    pending,
    try_many,
)

_LINE_BREAK_END = re.compile(r"(\\|<br/?>)$", re.IGNORECASE)


def _default_para(line: Line) -> Res:
    line = line.trim_whitespace()
    if _LINE_BREAK_END.search(line.content):
        return Res(line, WRAP, pending=False, next=None, is_default=True)
    return Res(line, WRAP, pending=True, next=_default_para, is_default=True)


def _blank_line(line: Line) -> Res | None:
    return finished(line, NO_WRAP) if line.is_blank() else None


def _match_finished(pattern: re.Pattern[str]) -> TryParser:
    return lambda line: finished(line, NO_WRAP) if pattern.search(line.content) else None


_atx_heading = _match_finished(md_marker(r"#{1,6} "))
_setext_underline = _match_finished(md_marker(r"(?:=+|-+)\s*$"))
_thematic_break = _match_finished(
    md_marker(r"(?:\*\s*\*\s*(?:\*\s*)+|-\s*-\s*(?:-\s*)+|_\s*_\s*(?:_\s*)+)$")
)


def _fenced_code(line: Line) -> Res | None:
    for start, end in (
        (md_marker(r"(~{3,})"), md_marker(r"(~{3,})\s*$")),
        (md_marker(r"(`{3,})[^`]*$"), md_marker(r"(`{3,})\s*$")),
    ):
        m = start.search(line.content)
        if m:
            return pending(line, NO_WRAP, _fence_body(len(m[1]), end))
    return None


def _fence_body(marker_length: int, end: re.Pattern[str]) -> Callable[[Line], Res]:
    def parse(line: Line) -> Res:
        m = end.search(line.content)
        if m and len(m[1]) >= marker_length:
            return finished(line, NO_WRAP)
        return pending(line, NO_WRAP, parse)

    return parse


HTML_BLOCK_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd"
    "|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset"
    "|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta"
    "|nav|noframes|ol|optgroup|option|p|param|section|source|summary|table|tbody|td|tfoot"
    "|th|thead|title|tr|track|ul"
)
_HTML_TYPES_1_TO_6 = [
    (md_marker(start), re.compile(end, re.IGNORECASE))
    for start, end in (
        (r"<(script|pre|style)( |>|$)", r"</(script|pre|style)>"),
        (r"<!--", r"-->"),
        (r"<\?", r"\?>"),
        (r"<![A-Z]", r">"),
        (r"<!\[CDATA\[", r"]]>"),
        (rf"</?({HTML_BLOCK_TAGS})(\s|/?>|$)", r"^\s*$"),
    )
]


def until_match(end: re.Pattern[str], line: Line, start: int = 0) -> Res:
    """Keep lines unwrapped up to and including the first line where `end` matches."""
    if end.search(line.content, start):
        return finished(line, NO_WRAP)
    return pending(line, NO_WRAP, lambda nxt: until_match(end, nxt))


def _html_type_1_to_6(line: Line) -> Res | None:
    for start, end in _HTML_TYPES_1_TO_6:
        m = start.search(line.content)
        if m:
            return until_match(end, line, m.end())
    return None


def _indented_code_line(line: Line) -> Res | Prev:
    if not line.is_blank() and line.indent_length() < 4:
        return Prev(None)
    return pending(line, NO_WRAP, _indented_code_line)


def _indented_code(line: Line) -> Res | None:
    if line.is_blank():
        return None
    res = _indented_code_line(line)
    return res if isinstance(res, Res) else None


_TABLE_CELLS_ROW = md_marker(r"\S.*?[^\\]\|\s*\S")
_TABLE_SEPARATOR_ROW = md_marker(r"[|:-][ |:-]+$")


def _is_table_separator(line: Line) -> bool:
    c = line.content
    return bool(_TABLE_SEPARATOR_ROW.search(c)) and "|" in c and "-" in c


def _table_row(has_separator: bool) -> Callable[[Line], Res | Prev]:
    def parse(line: Line) -> Res | Prev:
        if not _TABLE_CELLS_ROW.search(line.content):
            return Prev(None)
        sep = has_separator or _is_table_separator(line)
        kind = NO_WRAP if sep else WRAP
        return Res(line, kind, pending=True, next=_table_row(sep), is_default=not sep)

    return parse


def _table(line: Line) -> Res | None:
    if not _TABLE_CELLS_ROW.search(line.content):
        return None
    return Res(
        line, WRAP, pending=True, next=_table_row(_is_table_separator(line)), is_default=True
    )


def _blank_out(start: int, remove: int, replacement: str) -> Callable[[str], str]:
    return lambda prefix: prefix[:start] + replacement + prefix[start + remove :]


_BLOCKQUOTE = md_marker(r"> ?")


def _blockquote(new_block: FirstLineParser) -> TryParser:
    def find_marker(line: Line) -> Line | None:
        m = _BLOCKQUOTE.search(line.content)
        return line.adjust_split(len(m[0])) if m else None

    def parse(line: Line) -> Res | None:
        inside = find_marker(line)
        if inside is None:
            return None
        return container(new_block, lambda p: p, find_marker)(inside)

    return parse


def indented_container(
    new_block: FirstLineParser, prefix_fn: Callable[[str], str], marker_len: int, indent: int
) -> Callable[[Line], Res]:
    """Container whose following lines must be indented by `indent` (lazy text excepted)."""

    def line_test(line: Line) -> Line | None:
        if not line.is_blank() and line.indent_length() < indent:
            return None
        return line.adjust_split(indent)

    def parse(line: Line) -> Res:
        return container(new_block, prefix_fn, line_test)(line.adjust_split(marker_len))

    return parse


_FOOTNOTE = md_marker(r"(\[\^\S+?\]:)( +)")


def _footnote(new_block: FirstLineParser) -> TryParser:
    def parse(line: Line) -> Res | None:
        m = _FOOTNOTE.search(line.content)
        if not m:
            return None
        prefix_fn = _blank_out(len(line.prefix), len(m[0]), "    ")
        return indented_container(new_block, prefix_fn, len(m[0]), 4)(line)

    return parse


_LIST_ITEM = md_marker(r"([-+*]|[0-9]{1,9}[.)])( +)")


def _list_item(new_block: FirstLineParser) -> TryParser:
    def parse(line: Line) -> Res | None:
        m = _LIST_ITEM.search(line.content)
        if not m:
            return None
        # More than 4 spaces after the marker starts an indented code block in the item.
        child_indent = len(m[0]) if len(m[2]) <= 4 else len(m[0]) - len(m[2]) + 1
        prefix_fn = _blank_out(len(line.prefix), child_indent, " " * child_indent)
        return indented_container(new_block, prefix_fn, child_indent, child_indent)(line)

    return parse


_LINK_REF_LABEL = md_marker(r"\[\s*\S.*?\]:\s*")


def _link_ref_def(para_interrupter: TryParser) -> TryParser:
    """Link reference definition: wraps like a paragraph, with continuation lines indented."""

    def wrap_res(res: Res) -> Res:
        nxt = next_line(res.next) if res.pending else first_line
        return Res(res.line, res.kind, res.pending, nxt, res.is_default)

    def first_line(line: Line) -> Res:
        if _LINK_REF_LABEL.search(line.content):
            return on_match(line)
        return para_interrupter(line) or wrap_res(_default_para(line))

    def next_line(para: Callable[[Line], Res]) -> Callable[[Line], Res | Prev]:
        def parse(line: Line) -> Res | Prev:
            if _LINK_REF_LABEL.search(line.content):
                return Prev(on_match(line))
            interrupter = para_interrupter(line)
            if interrupter is not None:
                return Prev(interrupter)
            return wrap_res(para(line))

        return parse

    def on_match(line: Line) -> Res:
        prefix_fn = _blank_out(len(line.prefix), line.indent_length(), "    ")
        res = wrap_res(_default_para(line.trim_whitespace()))
        return Res(res.line, Kind(True, prefix_fn), res.pending, res.next, res.is_default)

    return lambda line: on_match(line) if _LINK_REF_LABEL.search(line.content) else None


def markdown(
    interrupters: Sequence[TryParser] = (), block_starts: Sequence[TryParser] = ()
) -> FirstLineParser:
    """Build a document parser: optional front matter, then Markdown blocks.

    `interrupters` may start a block anywhere, including directly after paragraph text;
    `block_starts` only after a blank line or a finished block. Both take precedence over
    the built-in blocks.
    """

    def new_block(line: Line) -> Res:
        return try_new_block(line) or paragraph(line)

    def paragraph(line: Line) -> Res:
        res = _default_para(line)
        if res.pending:
            return Res(res.line, WRAP, True, paragraph_line, is_default=True)
        return Res(res.line, WRAP, False, new_block, is_default=True)

    def paragraph_line(line: Line) -> Res | Prev:
        interrupter = try_para_interrupter(line)
        return Prev(interrupter) if interrupter is not None else paragraph(line)

    containers = [_blockquote(new_block), _footnote(new_block), _list_item(new_block)]
    blockquote, footnote, list_item = containers
    try_para_interrupter = try_many(
        [
            _blank_line,
            *interrupters,
            _atx_heading,
            _setext_underline,
            _thematic_break,
            blockquote,
            footnote,
            list_item,
            _fenced_code,
            _html_type_1_to_6,
        ]
    )
    try_new_block = try_many(
        [
            _blank_line,
            *interrupters,
            *block_starts,
            _atx_heading,
            _thematic_break,
            blockquote,
            footnote,
            list_item,
            _fenced_code,
            _html_type_1_to_6,
            _link_ref_def(try_para_interrupter),
            _indented_code,
            _table,
        ]
    )
    body = container(new_block, lambda p: p, lambda line: line)

    front_matter_start = re.compile(r"^---\s*$")
    front_matter_end = re.compile(r"^---")

    def front_matter_line(line: Line) -> Res:
        if front_matter_end.search(line.content):
            return finished(line, NO_WRAP, body)
        return pending(line, NO_WRAP, front_matter_line)

    def document(line: Line) -> Res:
        if front_matter_start.search(line.content):
            return pending(line, NO_WRAP, front_matter_line)
        return body(line)

    return document
