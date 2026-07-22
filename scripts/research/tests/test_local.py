"""Tests for scout/local.py rg_cmd."""

from __future__ import annotations

from research.scout.local import _TYPE_ALIASES


def test_type_aliases_map_tsx_to_ts() -> None:
    assert _TYPE_ALIASES["tsx"] == "ts"


def test_type_aliases_map_jsx_to_js() -> None:
    assert _TYPE_ALIASES["jsx"] == "js"


def test_type_aliases_map_rs_to_rust() -> None:
    assert _TYPE_ALIASES["rs"] == "rust"


def test_type_aliases_map_kt_to_kotlin() -> None:
    assert _TYPE_ALIASES["kt"] == "kotlin"


def test_type_aliases_map_cs_to_csharp() -> None:
    assert _TYPE_ALIASES["cs"] == "csharp"


def test_type_aliases_passthrough_for_unknown() -> None:
    assert _TYPE_ALIASES.get("py", "py") == "py"
    assert _TYPE_ALIASES.get("go", "go") == "go"
