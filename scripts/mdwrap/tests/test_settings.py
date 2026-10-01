"""Wrap width and tab width resolution from repository config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from mdwrap._errors import MdwrapError
from mdwrap._settings import resolve_settings


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _md013(width: int) -> str:
    return f"config:\n  line-length:\n    line_length: {width}\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _write(tmp_path / ".editorconfig", "root = true\n")
    return tmp_path


def _width(target: Path, override: int | None = None) -> int | None:
    settings = resolve_settings(target, width_override=override)
    return None if settings is None else settings.width


def test_override_beats_all_config(repo: Path) -> None:
    _write(repo / ".markdownlint-cli2.yaml", _md013(100))
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\n")
    settings = resolve_settings(repo / "a.md", width_override=72)
    assert settings is not None
    assert (settings.width, settings.width_source) == (72, "--width")


def test_markdownlint_beats_nearer_editorconfig(repo: Path) -> None:
    _write(repo / ".markdownlint-cli2.yaml", _md013(100))
    _write(repo / "docs" / ".editorconfig", "[*]\nmax_line_length = 80\n")
    settings = resolve_settings(repo / "docs" / "a.md", width_override=None)
    assert settings is not None
    assert settings.width == 100
    assert settings.width_source == str(repo / ".markdownlint-cli2.yaml")


def test_editorconfig_alone(repo: Path) -> None:
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\n")
    assert _width(repo / "a.md") == 90


def test_nothing_configured(repo: Path) -> None:
    assert resolve_settings(repo / "a.md", width_override=None) is None


def test_nearest_markdownlint_file_wins(repo: Path) -> None:
    _write(repo / ".markdownlint.yaml", "line-length:\n  line_length: 100\n")
    _write(repo / "sub" / ".markdownlint.json", '{"MD013": {"line_length": 72}}')
    assert _width(repo / "sub" / "a.md") == 72


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ({".markdownlint-cli2.jsonc": 1, "package.json": 2, ".markdownlint.yaml": 3}, 1),
        ({".markdownlint-cli2.yaml": 1, "package.json": 2}, 1),
        ({"package.json": 2, ".markdownlint.jsonc": 3}, 2),
    ],
)
def test_same_directory_order(repo: Path, files: dict[str, int], expected: int) -> None:
    for name, width in files.items():
        rules = {"line-length": {"line_length": width}}
        if name == "package.json":
            body: object = {"markdownlint-cli2": {"config": rules}}
        elif "cli2" in name:
            body = {"config": rules}
        else:
            body = rules
        # JSON is valid YAML, so one serializer covers every format.
        _write(repo / name, json.dumps(body))
    assert _width(repo / "a.md") == expected


def test_jsonc_comments_and_trailing_commas(repo: Path) -> None:
    _write(
        repo / ".markdownlint-cli2.jsonc",
        '{\n  // comment\n  "config": { "MD013": { "line_length": 88, }, },\n}\n',
    )
    assert _width(repo / "a.md") == 88


def test_last_rule_key_wins(repo: Path) -> None:
    _write(
        repo / ".markdownlint.json",
        '{"MD013": {"line_length": 70}, "Line-Length": {"line_length": 75}}',
    )
    assert _width(repo / "a.md") == 75


@pytest.mark.parametrize(
    "markdownlint",
    [
        "line-length: false\n",
        "default: true\n",
        "line-length:\n  line_length: off\n",
    ],
)
def test_non_numeric_markdownlint_falls_through(repo: Path, markdownlint: str) -> None:
    _write(repo / ".markdownlint.yaml", markdownlint)
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\n")
    assert _width(repo / "a.md") == 90


def test_editorconfig_off_falls_through(repo: Path) -> None:
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = off\n")
    assert resolve_settings(repo / "a.md", width_override=None) is None


def test_relative_extends_inherits_and_is_overridden(repo: Path) -> None:
    _write(repo / "base" / "lint.yaml", "line-length:\n  line_length: 60\n")
    _write(repo / ".markdownlint.yaml", "extends: base/lint.yaml\n")
    assert _width(repo / "a.md") == 60
    _write(repo / ".markdownlint.yaml", "extends: base/lint.yaml\nMD013:\n  line_length: 65\n")
    assert _width(repo / "a.md") == 65


def test_package_extends_is_ignored(repo: Path) -> None:
    _write(repo / ".markdownlint.yaml", "extends: markdownlint/style/prettier\n")
    assert resolve_settings(repo / "a.md", width_override=None) is None


def test_editorconfig_section_matches_extension(repo: Path) -> None:
    _write(repo / ".editorconfig", "root = true\n[*.md]\nmax_line_length = 90\n")
    assert _width(repo / "a.md") == 90
    assert _width(repo / "a.mdx") is None


def test_editorconfig_root_stops_search(repo: Path) -> None:
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\n")
    _write(repo / "inner" / ".editorconfig", "root = true\n")
    assert _width(repo / "inner" / "a.md") is None


def test_tab_width(repo: Path) -> None:
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\nindent_size = 2\n")
    settings = resolve_settings(repo / "a.md", width_override=None)
    assert settings is not None
    assert settings.tab_width == 2
    _write(repo / ".editorconfig", "root = true\n[*]\nmax_line_length = 90\n")
    settings = resolve_settings(repo / "a.md", width_override=None)
    assert settings is not None
    assert settings.tab_width == 4


@pytest.mark.parametrize(
    ("name", "text"),
    [
        (".markdownlint-cli2.jsonc", "{ not json"),
        (".markdownlint.yaml", "line-length: [unclosed\n"),
        ("package.json", "{"),
        (".editorconfig", "root = true\n[*\nmax_line_length = 90\n"),
    ],
)
def test_malformed_config_names_file(repo: Path, name: str, text: str) -> None:
    path = _write(repo / name, text)
    with pytest.raises(MdwrapError, match=str(path)):
        resolve_settings(repo / "a.md", width_override=None)
