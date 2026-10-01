"""Find markdownlint's explicit `line-length` (MD013) `line_length` for a file.

Only an explicit number counts. A disabled rule, an absent value (markdownlint's implicit 80),
and non-numeric values all count as "not set", so the caller falls through to other sources.
JavaScript configs (`.cjs`/`.mjs`) and package-name `extends` are not evaluated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import json5
import yaml

from mdwrap._errors import MdwrapError

# Per-directory lookup order. The bool marks markdownlint-cli2 files, whose rule settings sit
# under a `config` key.
_CONFIG_FILES = (
    (".markdownlint-cli2.jsonc", True),
    (".markdownlint-cli2.yaml", True),
    ("package.json", True),
    (".markdownlint.jsonc", False),
    (".markdownlint.json", False),
    (".markdownlint.yaml", False),
    (".markdownlint.yml", False),
)
_RULE_KEYS = frozenset({"line-length", "md013"})


def _load(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        if path.name == "package.json":
            data = json.loads(text)
            return data.get("markdownlint-cli2") if isinstance(data, dict) else None
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(text)
        return json5.loads(text)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise MdwrapError(f"{path}: invalid markdownlint config: {exc}") from exc


def _rule_width(config: Any, path: Path, seen: frozenset[Path]) -> int | None:
    if not isinstance(config, dict):
        return None
    width = None
    extends = config.get("extends")
    # A path that is not a file is a package name, which is not resolved.
    base = (path.parent / extends).resolve() if isinstance(extends, str) else None
    if base is not None and base.is_file():
        if base in seen:
            raise MdwrapError(f"{path}: markdownlint extends cycle at {base}")
        width = _rule_width(_load(base), base, seen | {base})
    # The file's own rule setting replaces an inherited one, as in markdownlint.
    for key, value in config.items():
        if str(key).lower() in _RULE_KEYS:
            number = value.get("line_length") if isinstance(value, dict) else None
            valid = isinstance(number, int) and not isinstance(number, bool) and number > 0
            width = number if valid else None
    return width


def find_line_length(start: Path) -> tuple[int, Path] | None:
    """Search `start` and its ancestors; return the nearest explicit width and its file."""
    for directory in (start, *start.parents):
        for name, is_cli2 in _CONFIG_FILES:
            path = directory / name
            if not path.is_file():
                continue
            config = _load(path)
            if is_cli2:
                config = config.get("config") if isinstance(config, dict) else None
            width = _rule_width(config, path, frozenset({path.resolve()}))
            if width is not None:
                return width, path
    return None
