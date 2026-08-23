"""Budget reservation and tracking."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from diskcache import Cache

MAX_CALLS: int = int(os.environ.get("RESEARCH_BUDGET_LIMIT") or 20)
CHECKPOINT_AT: int = MAX_CALLS // 2  # mid-session assessment
WARNING_AT: int = MAX_CALLS - 3  # final warning

_COUNT_KEY = "budget:count"
_SEEN_PREFIX = "seen:"


def budget_message(count: int) -> str:
    """Return a budget message for the current call count."""
    remaining = MAX_CALLS - count
    counter = f"[budget: {count}/{MAX_CALLS} calls used, {remaining} remaining]"

    if remaining < 0:
        return (
            f"\n=== BUDGET EXCEEDED ({MAX_CALLS}/{MAX_CALLS} calls used) ===\n"
            "You MUST synthesize your answer NOW from what you have gathered.\n"
            "No more tool calls will be executed."
        )
    if count == CHECKPOINT_AT:
        return (
            f"\n=== CHECKPOINT: {count}/{MAX_CALLS} calls used, "
            f"{remaining} remaining ===\n"
            "Stop and assess: can you answer the question now?\n"
            "If yes, synthesize. If not, identify the ONE specific "
            "gap that remains."
        )
    if count == WARNING_AT:
        return (
            f"\n=== WARNING: {count}/{MAX_CALLS} calls used, "
            f"{remaining} remaining ===\n"
            "Synthesize your answer NOW. Do not launch another batch.\n"
            "A later call requires --critical and one named blocking gap."
        )
    return f"\n{counter}"


def _session_key(key: str) -> str | None:
    """Scope a budget key to the opt-in research session."""
    from research._cache import get_session_id

    session_id = get_session_id()
    return f"budget:{session_id}:{key}" if session_id else None


def budget_reserve(
    cache: Cache,
    cached_url: str | None = None,
    critical: bool = False,
) -> None:
    """Reserve a budget slot and print the footer.

    Called BEFORE the tool performs any work so the printed counter reflects
    invocation order. Parallel callers serialize inside cache.transact().

    If cached_url was already seen this session, no slot is consumed.
    On budget exhaustion, prints the message then exits 1.
    """
    count_key = _session_key(_COUNT_KEY)
    if count_key is None:
        return
    seen_key = _session_key(f"{_SEEN_PREFIX}{cached_url}") if cached_url else None

    with cache.transact():
        count = cache.get(count_key, 0)

        if seen_key and seen_key in cache:
            remaining = MAX_CALLS - count
            click.echo(
                f"\n[cache hit; budget unchanged at {count}/{MAX_CALLS} used, "
                f"{remaining} remaining]"
            )
            return

        if count >= MAX_CALLS:
            click.echo(budget_message(MAX_CALLS + 1))
            sys.exit(1)

        if count >= WARNING_AT and not critical:
            click.echo(
                f"\n=== CRITICAL RESERVE ({count}/{MAX_CALLS} calls used) ===\n"
                f"The final {MAX_CALLS - count} calls are reserved. Synthesize now.\n"
                "Use --critical for one specific gap that prevents an answer."
            )
            sys.exit(1)

        count += 1
        cache.set(count_key, count, expire=24 * 3600)
        if seen_key:
            cache.set(seen_key, True, expire=24 * 3600)
        click.echo(budget_message(count))


def budget_refund(cache: Cache, cached_url: str | None = None) -> None:
    """Return a budget slot after a failed tool call.

    Reverses a prior budget_reserve: decrements count and removes the seen
    key if one was recorded. Prints a notice to stderr so the agent sees it.
    """
    count_key = _session_key(_COUNT_KEY)
    if count_key is None:
        return
    seen_key = _session_key(f"{_SEEN_PREFIX}{cached_url}") if cached_url else None

    with cache.transact():
        count = cache.get(count_key, 0)
        if count <= 0:
            return
        count -= 1
        cache.set(count_key, count, expire=24 * 3600)
        if seen_key and seen_key in cache:
            cache.delete(seen_key)

    remaining = MAX_CALLS - count
    click.echo(
        f"[refund: call failed; budget restored to {count}/{MAX_CALLS} used, "
        f"{remaining} remaining]",
        err=True,
    )


def budget_cache_hit(cache: Cache, cached_url: str | None = None) -> None:
    """Report a cache hit and mark a cached URL as retrieved this session."""
    count_key = _session_key(_COUNT_KEY)
    if count_key is None:
        click.echo("\n[cache hit; no budget session active]")
        return
    seen_key = _session_key(f"{_SEEN_PREFIX}{cached_url}") if cached_url else None

    with cache.transact():
        count = cache.get(count_key, 0)
        if seen_key:
            cache.set(seen_key, True, expire=24 * 3600)
    remaining = MAX_CALLS - count
    click.echo(
        f"\n[cache hit; budget unchanged at {count}/{MAX_CALLS} used, {remaining} remaining]"
    )


def get_count(cache: Cache) -> int:
    """Return current call count."""
    count_key = _session_key(_COUNT_KEY)
    return cache.get(count_key, 0) if count_key else 0


def format_status(cache: Cache) -> str:
    """Return status string for status command."""
    count_key = _session_key(_COUNT_KEY)
    if count_key is None:
        return "No budget session active."
    count = cache.get(count_key, 0)
    remaining = MAX_CALLS - count
    lines = [f"{count}/{MAX_CALLS} calls used, {remaining} remaining"]
    seen_prefix = _session_key(_SEEN_PREFIX)
    url_count = sum(1 for k in cache if isinstance(k, str) and k.startswith(seen_prefix or ""))
    if url_count:
        lines.append(f"cached URLs: {url_count}")
    if WARNING_AT <= count < MAX_CALLS:
        lines.append(f"critical reserve: {MAX_CALLS - count} calls")
    return "\n".join(lines)
