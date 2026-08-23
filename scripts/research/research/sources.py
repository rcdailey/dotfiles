"""Source ledger reporting command."""

from __future__ import annotations

import click

from research._source_ledger import get_sources


@click.command()
def cli() -> None:
    """Print every source URL retrieved in this research session."""
    sources = get_sources()
    if not sources:
        click.echo("No source URLs retrieved.")
        return
    click.echo("\n".join(f"{index}. {url}" for index, url in enumerate(sources, 1)))
