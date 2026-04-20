"""Status subcommand for budget reporting."""

from __future__ import annotations

import click

from research._budget import format_status
from research._cache import get_cache


@click.command()
def cli() -> None:
    """Print current budget usage."""
    cache = get_cache()
    click.echo(format_status(cache))
