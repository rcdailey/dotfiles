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
    if remaining < 0:
        return (
            f"\n=== BUDGET EXHAUSTED ({MAX_CALLS}/{MAX_CALLS} calls used; not a tool failure) ===\n"
            "This call did not run. Synthesize from the evidence gathered."
        )
    if count == CHECKPOINT_AT:
        return (
            f"\n=== CHECKPOINT: budget call {count} of {MAX_CALLS}; {remaining} remain ===\n"
            "Reassess every pending evidence track. Synthesize tracks that are supported; "
            "spend the rest only on tracks that still lack required evidence."
        )
    if count == WARNING_AT:
        return (
            f"\n=== WARNING: budget call {count} of {MAX_CALLS}; {remaining} remain ===\n"
            "Synthesize now. Later calls require `critical` and one named blocking gap."
        )
    return f"\n[budget call {count} of {MAX_CALLS}; {remaining} remain]"


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
    When the budget or its reserve blocks the call, prints the guard and exits 0: the guard is a
    budget decision, not a tool failure, so it stays out of the error ledger.
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
            sys.exit(0)

        if count >= WARNING_AT and not critical:
            click.echo(
                f"\n=== RESERVED ({count}/{MAX_CALLS} calls used; not a tool failure) ===\n"
                f"This call did not run. The final {MAX_CALLS - count} calls are reserved; "
                "synthesize now, or retry with `critical` for one named blocking gap."
            )
            sys.exit(0)

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
