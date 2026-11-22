"""Goal recording command: the first call of every research session."""

from __future__ import annotations

import sys

import click

from research._budget import MAX_CALLS, get_count
from research._cache import get_cache, get_session_id
from research._goals import add_goals


@click.command()
@click.argument("goals", nargs=-1, required=True)
def cli(goals: tuple[str, ...]) -> None:
    """Record research goals, one per requested fact or track; goals can be added, not removed."""
    if get_session_id() is None:
        click.echo("error: goals need a research session (OPENCODE_SESSION_ID)", err=True)
        sys.exit(2)
    recorded = add_goals(goals)
    click.echo("Goals:")
    click.echo("\n".join(f"{n}. {goal}" for n, goal in enumerate(recorded, 1)))
    click.echo(f"\n[budget {get_count(get_cache())} of {MAX_CALLS} used]")
