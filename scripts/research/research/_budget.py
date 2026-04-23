"""Budget reservation and tracking."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from diskcache import Cache

MAX_CALLS = 15
CHECKPOINT_AT = MAX_CALLS // 2  # 7: mid-session assessment
WARNING_AT = MAX_CALLS - 3  # 12: final warning

_COUNT_KEY = "count"
_URL_PREFIX = "url:"


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
            "Begin synthesizing your answer NOW. Use remaining calls "
            "only for critical gaps."
        )
    return f"\n{counter}"


def budget_reserve(cache: Cache, cached_url: str | None = None) -> None:
    """Reserve a budget slot and print the footer.

    Called BEFORE the tool performs any work so the printed counter reflects
    invocation order. Parallel callers serialize inside cache.transact().

    If cached_url was already seen this session, no slot is consumed.
    On budget exhaustion, prints the message then exits 1.
    """
    url_key = f"{_URL_PREFIX}{cached_url}" if cached_url else None

    with cache.transact():
        count = cache.get(_COUNT_KEY, 0)

        if url_key and url_key in cache:
            remaining = MAX_CALLS - count
            print(
                f"\n[cache hit; budget unchanged at {count}/{MAX_CALLS} used, "
                f"{remaining} remaining]",
                flush=True,
            )
            return

        count += 1
        cache.set(_COUNT_KEY, count)
        if url_key:
            cache.set(url_key, True)
        print(budget_message(count), flush=True)

    if count > MAX_CALLS:
        sys.exit(1)


def get_count(cache: Cache) -> int:
    """Return current call count."""
    return cache.get(_COUNT_KEY, 0)


def format_status(cache: Cache) -> str:
    """Return status string for status command."""
    count = cache.get(_COUNT_KEY, 0)
    remaining = MAX_CALLS - count
    lines = [f"{count}/{MAX_CALLS} calls used, {remaining} remaining"]
    url_count = sum(1 for k in cache if isinstance(k, str) and k.startswith(_URL_PREFIX))
    if url_count:
        lines.append(f"cached URLs: {url_count}")
    return "\n".join(lines)
