"""Public formatting entry point."""

from __future__ import annotations

import enum

from mdwrap._blocks import collect_blocks
from mdwrap._extensions import (
    MARKDOWN_INTERRUPTERS,
    MDX_BLOCK_STARTS,
    MDX_INTERRUPTERS,
    mdx_unbreakable,
)
from mdwrap._markdown import markdown
from mdwrap._reflow import reflow
from mdwrap._spans import markdown_unbreakable


class Dialect(enum.Enum):
    MARKDOWN = "markdown"
    MDX = "mdx"


def _mdx_unbreakable(text: str) -> frozenset[int]:
    return markdown_unbreakable(text) | mdx_unbreakable(text)


def rewrap(text: str, *, width: int, tab_width: int, dialect: Dialect) -> str:
    """Reflow every paragraph in `text` (LF line endings) to at most `width` columns.

    Lines outside paragraphs are returned byte-for-byte.
    """
    if dialect is Dialect.MDX:
        parser = markdown(MDX_INTERRUPTERS, MDX_BLOCK_STARTS)
        unbreakable = _mdx_unbreakable
    else:
        parser = markdown(MARKDOWN_INTERRUPTERS)
        unbreakable = markdown_unbreakable
    out: list[str] = []
    for kind, lines in collect_blocks(parser, text.split("\n")):
        if not kind.wrap:
            out.extend(line.text for line in lines)
            continue
        prefixes = [line.prefix for line in lines]
        if len(prefixes) == 1:
            prefixes.append(kind.prefix_fn(prefixes[0]))
        contents = [line.content for line in lines]
        out.extend(reflow(prefixes, contents, width, tab_width, unbreakable))
    return "\n".join(out)
