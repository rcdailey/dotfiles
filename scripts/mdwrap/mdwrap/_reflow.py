"""Paragraph reflow: join a block's lines, then break them at the wrap width.

Column widths follow Rewrap: tabs advance to the next tab stop, East Asian wide characters
count as 2 columns, and other control characters count as 0.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

# Characters that, under Chinese/Japanese line-breaking rules, may not start or end a line.
_CJ_NO_START = frozenset(
    "})]?,;¢°′″‰℃、。｡､￠，．：；？！％・･ゝゞヽヾーァィゥェォッャュョヮヵヶぁ"
    "ぃぅぇぉっゃゅょゎゕゖㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇺㇻㇼㇽㇾㇿ々〻ｧｨｩｪｫｬｭｮｯｰ”〉》」』】〕）］｝｣"
)
_CJ_NO_END = frozenset("([{‘“〈《「『【〔（［｛｢£¥＄￡￥＋")

# Returns the string positions before which a line break is forbidden.
Unbreakable = Callable[[str], frozenset[int]]


def char_width(tab_width: int, column: int, ch: str) -> int:
    """Return the display width of `ch` when it starts at `column`."""
    cp = ord(ch)
    if ch == "\t":
        return tab_width - column % tab_width
    if cp < 0x20:
        return 0
    if 0x2E80 <= cp <= 0xD7AF or 0xF900 <= cp <= 0xFAFF or 0xFF01 <= cp <= 0xFF5E:
        return 2
    # Rewrap measures UTF-16 code units, so astral characters (emoji) occupy 2 columns.
    return 2 if cp > 0xFFFF else 1


def str_width(tab_width: int, text: str, offset: int = 0) -> int:
    """Return the display width of `text` when it starts at column `offset`."""
    column = offset
    for ch in text:
        column += char_width(tab_width, column, ch)
    return column - offset


def _is_whitespace(ch: str) -> bool:
    return ord(ch) <= 0x20 or ch == "\u3000"


def _is_cj(ch: str) -> bool:
    cp = ord(ch)
    return 0x3040 <= cp <= 0x30FF or 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF


def _can_break_between(c1: str, c2: str) -> bool:
    if _is_whitespace(c1) or _is_whitespace(c2):
        return True
    if c1 in _CJ_NO_END or c2 in _CJ_NO_START:
        return False
    return _is_cj(c1) or _is_cj(c2)


def _concat(contents: Sequence[str]) -> str:
    """Join lines with single spaces; a line ending in two spaces keeps its hard break."""
    acc = contents[0]
    for line in contents[1:]:
        if not line or not acc:
            continue
        acc = acc + "\n" if acc.endswith("  ") else acc.rstrip()
        joiner = acc[-1] != "\n" and not _is_cj(acc[-1]) and not _is_cj(line[0])
        acc = acc + " " + line if joiner else acc + line
    return acc


def reflow(
    prefixes: Sequence[str],
    contents: Sequence[str],
    width: int,
    tab_width: int,
    unbreakable: Unbreakable | None = None,
) -> list[str]:
    """Reflow one paragraph.

    Output line N gets `prefixes[N]`; lines past the end of `prefixes` reuse its last entry.
    A word longer than the width stays whole and overflows.
    """
    text = _concat(contents)
    protected = unbreakable(text) if unbreakable else frozenset()
    out: list[str] = []
    prefix_index = 0

    def emit(start: int, end: int | None) -> int:
        nonlocal prefix_index
        prefix = prefixes[prefix_index]
        prefix_index = min(prefix_index + 1, len(prefixes) - 1)
        if end is None:
            body = text[start:]
        elif text[end - 1] == "\n":
            body = text[start : end - 1]
        else:
            body = text[start:end].rstrip()
        out.append(prefix + body)
        return str_width(tab_width, prefixes[prefix_index])

    def find_break(line_start: int, pos: int) -> int:
        while pos != line_start:
            if pos not in protected and _can_break_between(text[pos - 1], text[pos]):
                return pos
            pos -= 1
        return line_start

    line_start = pos = 0
    column = str_width(tab_width, prefixes[0])
    while pos < len(text):
        ch = text[pos]
        if ch == "\n":
            column = emit(line_start, pos + 1)
            pos = line_start = pos + 1
            continue
        next_column = column + char_width(tab_width, column, ch)
        if next_column <= width or _is_whitespace(ch):
            column = next_column
            pos += 1
            continue
        break_pos = find_break(line_start, pos)
        if break_pos <= line_start:
            column = next_column
            pos += 1
            continue
        column = emit(line_start, break_pos)
        pos = line_start = break_pos
    emit(line_start, None)
    return out
