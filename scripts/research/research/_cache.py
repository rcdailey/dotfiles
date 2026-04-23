"""Diskcache wrapper and URL cache helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from diskcache import Cache

_BASE_CACHE_DIR = Path("/tmp/.research-cache")
_session_id = os.environ["RESEARCH_SESSION_ID"]
CACHE_DIR = _BASE_CACHE_DIR / _session_id
_URL_PREFIX = "url:"

_cache_singleton: Cache | None = None


def get_cache() -> Cache:
    """Return the process-wide Cache handle, opening it lazily."""
    global _cache_singleton
    if _cache_singleton is None:
        from diskcache import Cache as _Cache

        _cache_singleton = _Cache(str(CACHE_DIR))
    return _cache_singleton


def read_cached_content(url: str) -> str | None:
    """Return cached markdown for a URL, or None if unseen."""
    cache = get_cache()
    value = cache.get(f"{_URL_PREFIX}{url}")
    return value if isinstance(value, str) else None


def write_cached_content(url: str, content: str) -> None:
    """Persist fetched markdown so repeat fetches skip the network."""
    cache = get_cache()
    cache.set(f"{_URL_PREFIX}{url}", content)
