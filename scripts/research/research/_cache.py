"""Diskcache wrapper and URL cache helpers."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from research._errors import die

if TYPE_CHECKING:
    from diskcache import Cache

_BASE_CACHE_DIR = Path("/tmp/.research-cache")
_CONTENT_PREFIX = "content:"
_SESSION_MAX_AGE = 24 * 3600  # 24 hours

_cache_singleton: Cache | None = None


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


def get_cache() -> Cache:
    """Return the process-wide Cache handle, opening it lazily.

    Spawns a background thread on first open to clean stale sibling sessions.
    """
    global _cache_singleton
    if _cache_singleton is None:
        from diskcache import Cache as _Cache

        session_id = os.environ.get("RESEARCH_SESSION_ID")
        if not session_id:
            die("RESEARCH_SESSION_ID is not set")
        _cache_singleton = _Cache(str(_BASE_CACHE_DIR / session_id))
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
