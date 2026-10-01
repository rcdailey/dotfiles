"""Resolve the wrap width and tab width for a target file.

Width precedence: `--width`, then markdownlint's explicit `line_length`, then EditorConfig's
`max_line_length`. Each config source is searched from the target's directory upward, and a
tool-specific setting beats a generic one even when the generic file is nearer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import editorconfig

from mdwrap._errors import MdwrapError
from mdwrap._markdownlint import find_line_length

DEFAULT_TAB_WIDTH = 4


@dataclass(frozen=True)
class WrapSettings:
    width: int
    tab_width: int
    # `--width` or the config file that set the width, for diagnostics.
    width_source: str


def _positive_int(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() and int(value) > 0 else None


def resolve_settings(target: Path, *, width_override: int | None) -> WrapSettings | None:
    """Return settings for `target`, or None when nothing sets a width.

    `target` need not exist; for stdin, callers pass a synthetic path in the start directory.
    """
    target = target.absolute()
    try:
        props = editorconfig.get_properties(str(target))
    except editorconfig.EditorConfigError as exc:
        raise MdwrapError(f"{target}: invalid .editorconfig: {exc}") from exc
    tab_width = _positive_int(props.get("tab_width")) or DEFAULT_TAB_WIDTH

    if width_override is not None:
        return WrapSettings(width_override, tab_width, "--width")
    found = find_line_length(target.parent)
    if found is not None:
        return WrapSettings(found[0], tab_width, str(found[1]))
    width = _positive_int(props.get("max_line_length"))
    if width is not None:
        return WrapSettings(width, tab_width, ".editorconfig")
    return None
