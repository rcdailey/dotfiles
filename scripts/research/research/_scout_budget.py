"""Independent context budget for repository scout calls."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from diskcache import Cache

MAX_SCOUT_CALLS: int = int(os.environ.get("RESEARCH_SCOUT_LIMIT") or 20)
SCOUT_CHECKPOINT_AT: int = MAX_SCOUT_CALLS // 2
SCOUT_WARNING_AT: int = MAX_SCOUT_CALLS - 3

_COUNT_KEY = "scout:count"


def _session_key() -> str | None:
    from research._cache import get_session_id

    session_id = get_session_id()
    return f"budget:{session_id}:{_COUNT_KEY}" if session_id else None


def scout_budget_reserve(cache: Cache, critical: bool = False) -> None:
    """Reserve one scout call without affecting the paid web/PDF budget."""
    count_key = _session_key()
    if count_key is None:
        return

    with cache.transact():
        count = cache.get(count_key, 0)
        if count >= MAX_SCOUT_CALLS:
            click.echo(
                f"\n=== SCOUT BUDGET EXCEEDED "
                f"({MAX_SCOUT_CALLS}/{MAX_SCOUT_CALLS} calls used) ===\n"
                "Synthesize from the repository evidence already gathered."
            )
            sys.exit(1)

        if count >= SCOUT_WARNING_AT and not critical:
            click.echo(
                f"\n=== SCOUT CRITICAL RESERVE "
                f"({count}/{MAX_SCOUT_CALLS} calls used) ===\n"
                f"The final {MAX_SCOUT_CALLS - count} calls are reserved. Synthesize now.\n"
                "Use `research scout --critical ...` for one named blocking gap."
            )
            sys.exit(1)

        count += 1
        cache.set(count_key, count, expire=24 * 3600)

    remaining = MAX_SCOUT_CALLS - count
    if count == SCOUT_CHECKPOINT_AT:
        click.echo(
            f"\n=== SCOUT CHECKPOINT: {count}/{MAX_SCOUT_CALLS} calls used, "
            f"{remaining} remaining ===\n"
            "Stop and identify the smallest remaining repository evidence gap."
        )
        return
    if count == SCOUT_WARNING_AT:
        click.echo(
            f"\n=== SCOUT WARNING: {count}/{MAX_SCOUT_CALLS} calls used, "
            f"{remaining} remaining ===\n"
            "Synthesize now. Later scout calls require --critical."
        )
        return
    click.echo(f"\n[scout budget: {count}/{MAX_SCOUT_CALLS} calls used, {remaining} remaining]")


def get_scout_count(cache: Cache) -> int:
    """Return the current session's scout call count."""
    count_key = _session_key()
    return cache.get(count_key, 0) if count_key else 0


def format_scout_status(cache: Cache) -> str:
    """Return the independent scout budget status."""
    count_key = _session_key()
    if count_key is None:
        return "No scout budget session active."
    count = cache.get(count_key, 0)
    remaining = MAX_SCOUT_CALLS - count
    status = f"{count}/{MAX_SCOUT_CALLS} calls used, {remaining} remaining"
    if SCOUT_WARNING_AT <= count < MAX_SCOUT_CALLS:
        status += f"\ncritical reserve: {MAX_SCOUT_CALLS - count} calls"
    return status
