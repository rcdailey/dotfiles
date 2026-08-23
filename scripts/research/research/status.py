"""Status subcommand for budget reporting."""

from __future__ import annotations

import click

from research._budget import format_status
from research._cache import get_cache
from research._error_ledger import get_errors
from research._source_ledger import get_sources


@click.command()
def cli() -> None:
    """Print current budget usage."""
    cache = get_cache()
    click.echo(f"web/pdf:\n{format_status(cache)}")
    click.echo(f"\nretrieved sources: {len(get_sources())}")
    click.echo(f"\nrecorded errors: {len(get_errors())}")
