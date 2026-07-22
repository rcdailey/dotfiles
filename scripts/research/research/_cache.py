"""Diskcache wrapper and URL cache helpers."""

from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from research._errors import die

if TYPE_CHECKING:
    from diskcache import Cache

_BASE_CACHE_DIR = Path("/tmp/.research-cache")
_CONTENT_PREFIX = "content:"
_SESSION_MAX_AGE = 24 * 3600  # 24 hours

_cache_singleton: Cache | _InMemoryCache | None = None


class _InMemoryCache:
    """Fallback when diskcache fails (disk I/O errors, corruption)."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def __contains__(self, key: object) -> bool:
        return key in self._store

    def __iter__(self):
        return iter(list(self._store.keys()))

    @contextlib.contextmanager
    def transact(self) -> Generator[None, None, None]:
        yield


def _cleanup_stale_sessions(current_session: str) -> None:
    """Remove session directories older than 24 hours (runs in background)."""
    import shutil
    import time

    now = time.time()
    if not _BASE_CACHE_DIR.exists():
        return
    for session_dir in _BASE_CACHE_DIR.iterdir():
        if not session_dir.is_dir() or session_dir.name == current_session:
            continue
        try:
            age = now - session_dir.stat().st_mtime
            if age > _SESSION_MAX_AGE:
                shutil.rmtree(session_dir, ignore_errors=True)
        except OSError:
            pass


def get_cache() -> Cache | _InMemoryCache:
    """Return the process-wide Cache handle, opening it lazily.

    Spawns a background thread on first open to clean stale sibling sessions.
    Falls back to an in-memory cache if diskcache initialization fails.
    """
    global _cache_singleton
    if _cache_singleton is None:
        session_id = os.environ.get("RESEARCH_SESSION_ID")
        if not session_id:
            die("RESEARCH_SESSION_ID is not set")
        try:
            from diskcache import Cache as _Cache

            _cache_singleton = _Cache(str(_BASE_CACHE_DIR / session_id))
        except Exception:
            click.echo("[warning: cache unavailable; using in-memory fallback]", err=True)
            _cache_singleton = _InMemoryCache()
        threading.Thread(
            target=_cleanup_stale_sessions,
            args=(session_id,),
            daemon=True,
        ).start()
    return _cache_singleton


def read_cached_content(url: str) -> str | None:
    """Return cached markdown for a URL, or None if unseen."""
    cache = get_cache()
    value = cache.get(f"{_CONTENT_PREFIX}{url}")
    return value if isinstance(value, str) else None


def write_cached_content(url: str, content: str) -> None:
    """Persist fetched markdown so repeat fetches skip the network."""
    cache = get_cache()
    cache.set(f"{_CONTENT_PREFIX}{url}", content)
