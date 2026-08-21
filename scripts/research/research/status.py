"""Status subcommand for budget reporting."""

from __future__ import annotations

import click

from research._budget import format_status
from research._cache import get_cache
from research._error_ledger import get_errors
from research._scout_budget import format_scout_status


@click.command()
def cli() -> None:
    """Print current budget usage."""
    cache = get_cache()
    click.echo(f"web/pdf:\n{format_status(cache)}")
    click.echo(f"\nscout:\n{format_scout_status(cache)}")
    click.echo(f"\nrecorded errors: {len(get_errors())}")
