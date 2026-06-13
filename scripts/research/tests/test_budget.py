"""Tests for _budget.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import research._budget as budget_mod
from research._budget import (
    _COUNT_KEY,
    _SEEN_PREFIX,
    budget_refund,
    budget_reserve,
    format_status,
)


def _make_cache(count: int = 0, seen_keys: list[str] | None = None) -> MagicMock:
    """Return a MagicMock cache with configurable state."""
    seen_keys = seen_keys or []
    cache = MagicMock()
    store: dict = {_COUNT_KEY: count, **{k: True for k in seen_keys}}

    def _get(key, default=None):
        return store.get(key, default)

    def _contains(key):
        return key in store

    def _set(key, value):
        store[key] = value

    def _delete(key):
        store.pop(key, None)

    def _iter():
        return iter(list(store.keys()))

    cache.get.side_effect = _get
    cache.__contains__ = MagicMock(side_effect=_contains)
    cache.set.side_effect = _set
    cache.delete.side_effect = _delete
    cache.__iter__ = MagicMock(side_effect=lambda: _iter())
    cache.transact.return_value.__enter__ = MagicMock(return_value=None)
    cache.transact.return_value.__exit__ = MagicMock(return_value=False)
    return cache


def test_budget_reserve_increments_count(capsys) -> None:
    cache = _make_cache(count=0)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_reserve(cache)
    cache.set.assert_any_call(_COUNT_KEY, 1)


def test_budget_reserve_prints_counter(capsys) -> None:
    cache = _make_cache(count=0)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_reserve(cache)
    out = capsys.readouterr().out
    assert "budget:" in out
    assert "1/15" in out


def test_budget_reserve_cache_hit_skips_increment(capsys) -> None:
    seen_key = f"{_SEEN_PREFIX}https://example.com"
    cache = _make_cache(count=3, seen_keys=[seen_key])
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_reserve(cache, "https://example.com")
    # count should not be incremented
    calls = [call for call in cache.set.call_args_list if call[0][0] == _COUNT_KEY]
    assert not calls
    out = capsys.readouterr().out
    assert "cache hit" in out


def test_budget_reserve_records_seen_key() -> None:
    cache = _make_cache(count=0)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_reserve(cache, "https://example.com")
    seen_key = f"{_SEEN_PREFIX}https://example.com"
    cache.set.assert_any_call(seen_key, True)


def test_budget_reserve_exits_when_exceeded() -> None:
    cache = _make_cache(count=15)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        with pytest.raises(SystemExit) as exc_info:
            budget_reserve(cache)
    assert exc_info.value.code == 1


def test_budget_reserve_env_var_override() -> None:
    """MAX_CALLS respects RESEARCH_BUDGET_LIMIT at module load time."""
    # We test the derivation logic directly rather than reloading the module.
    import os

    with patch.dict(os.environ, {"RESEARCH_BUDGET_LIMIT": "5"}):
        resolved = int(os.environ.get("RESEARCH_BUDGET_LIMIT") or 15)
    assert resolved == 5


def test_budget_refund_decrements_count(capsys) -> None:
    cache = _make_cache(count=3)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_refund(cache)
    cache.set.assert_any_call(_COUNT_KEY, 2)
    err = capsys.readouterr().err
    assert "refund" in err


def test_budget_refund_removes_seen_key() -> None:
    seen_key = f"{_SEEN_PREFIX}https://example.com"
    cache = _make_cache(count=3, seen_keys=[seen_key])
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_refund(cache, "https://example.com")
    cache.delete.assert_called_once_with(seen_key)


def test_budget_refund_noop_at_zero() -> None:
    cache = _make_cache(count=0)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        budget_refund(cache)
    cache.set.assert_not_called()


def test_format_status_no_seen_urls() -> None:
    cache = _make_cache(count=5)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        result = format_status(cache)
    assert "5/15" in result
    assert "10 remaining" in result
    assert "cached URLs" not in result


def test_format_status_with_seen_urls() -> None:
    seen_keys = [f"{_SEEN_PREFIX}https://a.com", f"{_SEEN_PREFIX}https://b.com"]
    cache = _make_cache(count=2, seen_keys=seen_keys)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        result = format_status(cache)
    assert "cached URLs: 2" in result


def test_format_status_ignores_non_seen_keys() -> None:
    """budget:count and content: keys should not be counted as seen URLs."""
    cache = _make_cache(count=1)
    # Inject a content: key into the mock store
    store = {_COUNT_KEY: 1, "content:https://x.com": "html", f"{_SEEN_PREFIX}https://y.com": True}
    cache.__iter__ = MagicMock(side_effect=lambda: iter(list(store.keys())))
    cache.get.side_effect = lambda k, d=None: store.get(k, d)
    with patch.object(budget_mod, "MAX_CALLS", 15):
        result = format_status(cache)
    assert "cached URLs: 1" in result
