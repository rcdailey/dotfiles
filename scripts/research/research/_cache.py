"""Session budget storage and shared, expiring result caches."""

from __future__ import annotations

import contextlib
import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit

import click

if TYPE_CHECKING:
    from diskcache import Cache

_BASE_CACHE_DIR = Path("/tmp/.research-cache")
_CONTENT_PREFIX = "content:"
_SEARCH_PREFIX = "search:"
_CACHE_TTL = 24 * 3600

_cache_singleton: Cache | _InMemoryCache | None = None


class _InMemoryCache:
    """Fallback when diskcache fails (disk I/O errors, corruption)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        item = self._store.get(key)
        if item is None:
            return default
        value, expires_at = item
        if expires_at is None or expires_at > time.monotonic():
            return value
        self.delete(key)
        return default

    def set(self, key: str, value: Any, expire: int | None = None) -> None:
        expires_at = time.monotonic() + expire if expire is not None else None
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self.get(key) is not None

    def __iter__(self):
        return iter([key for key in self._store if key in self])

    @contextlib.contextmanager
    def transact(self) -> Generator[None, None, None]:
        yield


def get_cache() -> Cache | _InMemoryCache:
    """Return the shared cache, falling back to memory if it cannot open."""
    global _cache_singleton
    if _cache_singleton is None:
        try:
            from diskcache import Cache as _Cache

            _cache_singleton = _Cache(str(_BASE_CACHE_DIR))
        except Exception:  # noqa: BLE001
            click.echo("[warning: cache unavailable; using in-memory fallback]", err=True)
            _cache_singleton = _InMemoryCache()
    return _cache_singleton


def get_session_id() -> str | None:
    """Return the opt-in budget session identifier, if supplied."""
    return os.environ.get("RESEARCH_SESSION_ID") or None


def cache_url(url: str) -> str:
    """Return a URL cache identity that keeps queries and ignores fragments."""
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))


def read_cached_content(url: str) -> str | None:
    """Return cached markdown for a URL, or None if unseen."""
    cache = get_cache()
    value = cache.get(f"{_CONTENT_PREFIX}{cache_url(url)}")
    return value if isinstance(value, str) else None


def write_cached_content(url: str, content: str) -> None:
    """Persist fetched markdown so repeat fetches skip the network."""
    cache = get_cache()
    cache.set(f"{_CONTENT_PREFIX}{cache_url(url)}", content, expire=_CACHE_TTL)


def read_cached_search(key: str) -> str | None:
    """Return a shared cached search rendering, if available."""
    value = get_cache().get(f"{_SEARCH_PREFIX}{key}")
    return value if isinstance(value, str) else None


def write_cached_search(key: str, content: str) -> None:
    """Cache a rendered search response for all callers for 24 hours."""
    get_cache().set(f"{_SEARCH_PREFIX}{key}", content, expire=_CACHE_TTL)
