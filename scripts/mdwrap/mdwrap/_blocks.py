"""Line-by-line Markdown block parser that splits a document into wrap and no-wrap blocks.

The design follows Rewrap's parser (dnut/Rewrap `core/Parsers_Markdown.fs`): each line is
fed to a parser that classifies it and returns the parser for the next line. Containers
(block quotes, list items, footnotes) move their markers into the line's prefix before
handing the rest of the line to an inner parser, so a wrapped paragraph keeps each
line's original prefix and indent ("paragraph shape").
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

PrefixFn = Callable[[str], str]


def _identity(prefix: str) -> str:
    return prefix


@dataclass(frozen=True, slots=True)
class Line:
    """A source line split into a non-wrapped prefix and the content still being parsed."""

    prefix: str
    content: str

    @staticmethod
    def split_at(text: str, pos: int) -> Line:
        pos = min(pos, len(text))
        return Line(text[:pos], text[pos:])

    @property
    def text(self) -> str:
        return self.prefix + self.content

    def adjust_split(self, delta: int) -> Line:
        if not self.content:
            return self
        return Line.split_at(self.text, len(self.prefix) + delta)

    def trim_whitespace(self) -> Line:
        stripped = self.content.lstrip()
        return Line(self.prefix + self.content[: len(self.content) - len(stripped)], stripped)

    def indent_length(self) -> int:
        return len(self.content) - len(self.content.lstrip())

    def is_blank(self) -> bool:
        return not self.content.strip()


@dataclass(frozen=True, slots=True)
class Kind:
    """Whether a block is reflowed.

    `prefix_fn` derives the prefix for lines that wrapping adds to a one-line block, such as
    blanking a list marker into spaces.
    """

    wrap: bool
    prefix_fn: PrefixFn = _identity


NO_WRAP = Kind(wrap=False)
WRAP = Kind(wrap=True)


@dataclass(frozen=True, slots=True)
class Res:
    """Parse result for one line.

    A pending result continues its block, and `next` parses the following line of that
    block. A finished result ends its block, and `next` (when set) parses the line that
    starts the following block. `is_default` marks normal paragraph text, which may
    continue lazily into a container line that lacks the container's marker or indent.
    """

    line: Line
    kind: Kind
    pending: bool
    next: Callable | None
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class Prev:
    """Next-line result: the block ended on the previous line; `res` starts the next one."""

    res: Res | None


FirstLineParser = Callable[[Line], Res]
NextLineParser = Callable[[Line], "Res | Prev"]
TryParser = Callable[[Line], "Res | None"]


def pending(line: Line, kind: Kind, nxt: NextLineParser) -> Res:
    return Res(line, kind, pending=True, next=nxt)


def finished(line: Line, kind: Kind, nxt: FirstLineParser | None = None) -> Res:
    return Res(line, kind, pending=False, next=nxt)


def md_marker(pattern: str) -> re.Pattern[str]:
    """Compile `pattern` to match after at most 3 spaces of indent, ignoring case."""
    return re.compile(r"^ {0,3}" + pattern, re.IGNORECASE)


def try_many(parsers: Sequence[TryParser]) -> TryParser:
    def parse(line: Line) -> Res | None:
        for parser in parsers:
            res = parser(line)
            if res is not None:
                return res
        return None

    return parse


def _with_prefix_fn(prefix_fn: PrefixFn, res: Res) -> Res:
    if not res.kind.wrap:
        return res
    inner = res.kind.prefix_fn
    return dataclasses.replace(res, kind=Kind(wrap=True, prefix_fn=lambda p: prefix_fn(inner(p))))


def container(
    content: FirstLineParser,
    prefix_fn: PrefixFn,
    line_test: Callable[[Line], Line | None],
) -> FirstLineParser:
    """Build a container parser.

    `line_test` returns the line with the container's marker moved into its prefix, or None
    when the line does not belong to the container. A paragraph may still continue into such
    a line (lazy continuation).
    """

    def wrap_res(res: Res) -> Res:
        if res.pending:
            return dataclasses.replace(res, next=next_line(res.is_default, res.next))
        return dataclasses.replace(res, next=first_line(res.is_default, res.next))

    def first_line(was_para: bool, inner: FirstLineParser | None) -> FirstLineParser:
        def parse(line: Line) -> Res:
            inside = line_test(line)
            if inside is not None:
                return wrap_res((inner or content)(inside))
            if inner is not None and was_para:
                return wrap_res(inner(line))
            return (inner or content)(line)

        return parse

    def next_line(was_para: bool, inner: NextLineParser) -> NextLineParser:
        def parse(line: Line) -> Res | Prev:
            inside = line_test(line)
            if inside is not None:
                res = inner(inside)
                if isinstance(res, Res):
                    return wrap_res(res)
                return Prev(wrap_res(res.res or content(inside)))
            if not was_para:
                return Prev(None)
            res = inner(line)
            return wrap_res(res) if isinstance(res, Res) else res

        return parse

    return lambda line: _with_prefix_fn(prefix_fn, wrap_res(content(line)))


def collect_blocks(parser: FirstLineParser, lines: Sequence[str]) -> list[tuple[Kind, list[Line]]]:
    """Feed every line through `parser` and group the results into blocks."""
    blocks: list[tuple[Kind, list[Line]]] = []
    block_lines: list[Line] = []
    prev: Res | None = None
    nxt: FirstLineParser | None = None

    def start(res: Res) -> None:
        nonlocal prev, nxt, block_lines
        if res.pending:
            prev = res
            return
        blocks.append((res.kind, [*block_lines, res.line]))
        block_lines, prev, nxt = [], None, res.next

    for text in lines:
        line = Line("", text)
        if prev is None:
            start((nxt or parser)(line))
            continue
        res = prev.next(line)
        if isinstance(res, Res):
            block_lines.append(prev.line)
            start(res)
            continue
        blocks.append((prev.kind, [*block_lines, prev.line]))
        block_lines, prev = [], None
        start(res.res or parser(line))
    if prev is not None:
        blocks.append((prev.kind, [*block_lines, prev.line]))
    return blocks
