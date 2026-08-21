"""Error ledger reporting command."""

from __future__ import annotations

import click

from research._error_ledger import get_errors


@click.command()
def cli() -> None:
    """Print every failed invocation recorded in this research session."""
    errors = get_errors()
    if not errors:
        click.echo("No tool failures recorded.")
        return
    click.echo("\n\n".join(f"{index}. {error}" for index, error in enumerate(errors, 1)))
