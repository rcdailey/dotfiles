"""Tests for _cache.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from research._cache import _CONTENT_PREFIX, read_cached_content, write_cached_content


def _make_cache_mock(store: dict | None = None) -> MagicMock:
    store = store if store is not None else {}
    cache = MagicMock()
    cache.get.side_effect = lambda k, d=None: store.get(k, d)
    cache.set.side_effect = lambda k, v: store.update({k: v})
    return cache


def test_get_cache_missing_session_id() -> None:
    import research._cache as cache_mod

    cache_mod._cache_singleton = None
    with patch.dict("os.environ", {}, clear=True):
        # Ensure RESEARCH_SESSION_ID is absent
        import os

        os.environ.pop("RESEARCH_SESSION_ID", None)
        with pytest.raises(SystemExit):
            cache_mod.get_cache()
    cache_mod._cache_singleton = None


def test_get_cache_returns_cache_with_session_id() -> None:
    import research._cache as cache_mod

    cache_mod._cache_singleton = None
    mock_cache = MagicMock()
    with (
        patch("research._cache.threading.Thread") as mock_thread,
        patch("diskcache.Cache", return_value=mock_cache),
        patch.dict("os.environ", {"RESEARCH_SESSION_ID": "test-abc"}),
    ):
        mock_thread.return_value.start = MagicMock()
        result = cache_mod.get_cache()
    assert result is mock_cache
    cache_mod._cache_singleton = None


def test_get_cache_spawns_background_cleanup() -> None:
    import research._cache as cache_mod

    cache_mod._cache_singleton = None
    mock_cache = MagicMock()
    with (
        patch("research._cache.threading.Thread") as mock_thread,
        patch("diskcache.Cache", return_value=mock_cache),
        patch.dict("os.environ", {"RESEARCH_SESSION_ID": "test-xyz"}),
    ):
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance
        cache_mod.get_cache()
    mock_thread.assert_called_once()
    thread_instance.start.assert_called_once()
    cache_mod._cache_singleton = None


def test_get_cache_singleton() -> None:
    import research._cache as cache_mod

    existing = MagicMock()
    cache_mod._cache_singleton = existing
    result = cache_mod.get_cache()
    assert result is existing
    cache_mod._cache_singleton = None


def test_read_cached_content_hit() -> None:
    mock_cache = _make_cache_mock({f"{_CONTENT_PREFIX}https://x.com": "# Hello"})
    with patch("research._cache.get_cache", return_value=mock_cache):
        result = read_cached_content("https://x.com")
    assert result == "# Hello"


def test_read_cached_content_miss() -> None:
    mock_cache = _make_cache_mock()
    with patch("research._cache.get_cache", return_value=mock_cache):
        result = read_cached_content("https://x.com")
    assert result is None


def test_read_cached_content_wrong_type() -> None:
    mock_cache = _make_cache_mock({f"{_CONTENT_PREFIX}https://x.com": 42})
    with patch("research._cache.get_cache", return_value=mock_cache):
        result = read_cached_content("https://x.com")
    assert result is None


def test_write_cached_content_uses_content_prefix() -> None:
    store: dict = {}
    mock_cache = _make_cache_mock(store)
    with patch("research._cache.get_cache", return_value=mock_cache):
        write_cached_content("https://x.com", "content here")
    assert store.get(f"{_CONTENT_PREFIX}https://x.com") == "content here"
