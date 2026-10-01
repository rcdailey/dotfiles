"""Reader for Rewrap's example-based spec format (dnut/Rewrap `docs/specs/README.md`).

Each example is an indented block with input left of a `->` marker and expected output
right of it. `¦` marks the wrap column, `·` an explicit space, and `-→` a tab. A settings
blockquote (`> language: markdown, tabWidth: 2`) applies to the examples after it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from mdwrap._reflow import str_width


@dataclass(frozen=True)
class Example:
    file: str
    line: int
    settings: dict[str, str]
    input: list[str] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)
    width: int = 0
    has_selection: bool = False
    error: str | None = None

    @property
    def id(self) -> str:
        return f"{self.file}:{self.line}"


_CLEANUPS = [
    (re.compile(r" ->(?=\s*$)"), "   "),
    (re.compile(r"-or-"), "    "),
    (re.compile(r"¦"), " "),
    (re.compile(r"[«»]"), ""),
    (re.compile(r"\s+$"), ""),
    (re.compile(r"·"), " "),
    (re.compile(r"-*→"), "\t"),
]


def _width(text: str) -> int:
    return str_width(1, text)


def _width_before(marker: str, text: str) -> int:
    pos = text.find(marker)
    return -1 if pos < 0 else _width(text[:pos])


def _split_at_width(col: int, text: str) -> tuple[str, str]:
    i = width = 0
    while True:
        if i > len(text) or width > col:
            pos = i - 1
            break
        if i >= len(text):
            pos = i
            break
        width += _width(text[i])
        i += 1
    return text[:pos], text[pos:]


def _remove_indent(lines: list[str]) -> list[str]:
    indents = [len(s) - len(s.lstrip()) for s in lines if s.strip()]
    n = min(indents, default=0)
    return [s[n:] for s in lines]


def _split_lines(marker: str, lines: list[str]) -> tuple[list[str], list[str] | None]:
    split_point = max(_width_before(marker, s) for s in lines)
    if split_point < 0:
        return _remove_indent(lines), None
    pairs = [_split_at_width(split_point + len(marker), s) for s in lines]
    return _remove_indent([a for a, _ in pairs]), _remove_indent([b for _, b in pairs])


def _wrap_column(lines: list[str]) -> int | None:
    cols = {_width_before("¦", s) for s in lines} - {-1}
    return cols.pop() if len(cols) == 1 else None


def _clean(lines: list[str]) -> list[str]:
    out = []
    for s in lines:
        for rx, rep in _CLEANUPS:
            s = rx.sub(rep, s)
        out.append(s)
    while out and not out[-1]:
        out.pop()
    return out


def _example(file: str, line: int, settings: dict[str, str], lines: list[str]) -> Example:
    lines = [s.removesuffix("<only>") for s in lines]
    inputs, outputs = _split_lines(" -> ", lines)
    if outputs is None:
        return Example(file, line, settings, error="no output")
    expected, alternative = _split_lines("-or-", outputs)
    groups = [inputs, expected] if alternative is None else [inputs, expected, alternative]
    cols = {_wrap_column(group) for group in groups}
    if len(cols) != 1 or None in cols:
        return Example(file, line, settings, error="inconsistent wrap column")
    return Example(
        file,
        line,
        settings,
        input=_clean(inputs),
        expected=_clean(expected),
        width=cols.pop(),
        has_selection=any(c in s for s in inputs for c in "«»"),
    )


def _settings(line: str) -> dict[str, str]:
    out = {}
    for pair in line[1:].split(","):
        key, sep, value = pair.partition(":")
        if sep:
            out[key.strip()] = value.strip().strip('"')
    return out


def read_examples(path: Path) -> list[Example]:
    examples: list[Example] = []
    settings: dict[str, str] = {}
    sample: list[str] | None = []
    start = 0

    def finish() -> None:
        if sample:
            examples.append(_example(path.name, start, settings, sample))

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("    "):
            if sample is not None:
                if not sample:
                    start = number
                sample.append(line)
        elif line.startswith("> "):
            settings, sample = _settings(line), None
        else:
            finish()
            sample = [] if not line else None
    finish()
    return examples
