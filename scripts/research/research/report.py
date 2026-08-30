"""Final source and error ledger report."""

from __future__ import annotations

import click

from research._error_ledger import get_errors
from research._source_ledger import get_sources


@click.command()
def cli() -> None:
    """Print retrieved sources and recorded failures."""
    sources = get_sources()
    click.echo("Sources:")
    if sources:
        click.echo("\n".join(f"{index}. {url}" for index, url in enumerate(sources, 1)))
    else:
        click.echo("No source URLs retrieved.")

    errors = get_errors()
    click.echo("\nErrors:")
    if errors:
        click.echo("\n\n".join(f"{index}. {error}" for index, error in enumerate(errors, 1)))
    else:
        click.echo("No tool failures recorded.")
