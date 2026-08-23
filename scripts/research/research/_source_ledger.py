"""Persistent per-session ledger of retrieved source URLs."""

from __future__ import annotations

import re
from collections.abc import Iterable

_SOURCES_KEY = "sources"
_EXPIRY_SECONDS = 24 * 3600
_URL_CHARS = r"A-Za-z0-9._~:/?#@!$&'*+,;=%-"


def _session_key() -> str | None:
    """Return the active session's source-ledger key."""
    from research._cache import get_session_id

    session_id = get_session_id()
    return f"research:{session_id}:{_SOURCES_KEY}" if session_id else None


def record_source(url: str) -> None:
    """Record one successfully retrieved URL for the active session."""
    record_sources([url])


def record_sources(urls: Iterable[str]) -> None:
    """Record successfully retrieved URLs, preserving first-seen order."""
    from research._cache import get_cache

    key = _session_key()
    if key is None:
        return
    additions = [url for url in urls if url]
    if not additions:
        return

    cache = get_cache()
    with cache.transact():
        sources = list(cache.get(key, []))
        seen = set(sources)
        for url in additions:
            if url in seen:
                continue
            sources.append(url)
            seen.add(url)
        cache.set(key, sources, expire=_EXPIRY_SECONDS)


def record_visible_sources(output: str, urls: Iterable[str]) -> None:
    """Record only source URLs present in rendered command output."""
    visible = (
        url
        for url in urls
        if re.search(rf"(?<![{_URL_CHARS}]){re.escape(url)}(?![{_URL_CHARS}])", output)
    )
    record_sources(visible)


def get_sources() -> list[str]:
    """Return retrieved source URLs for the active session."""
    from research._cache import get_cache

    key = _session_key()
    if key is None:
        return []
    return list(get_cache().get(key, []))
