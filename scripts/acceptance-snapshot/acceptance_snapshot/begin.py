"""Begin an acceptance snapshot iteration."""

from __future__ import annotations

import click

from acceptance_snapshot._errors import SnapshotError
from acceptance_snapshot._state import begin


@click.command()
@click.option("--base", help="Initial comparison revision.")
def cli(base: str | None) -> None:
    """Capture the candidate repository tree."""
    try:
        result = begin(base)
    except SnapshotError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1) from None
    click.echo(f"Iteration: {result.iteration}")
    click.echo(f"Previous tree: {result.previous_tree}")
    click.echo(f"Pending tree: {result.pending_tree}")
    click.echo("Changes:")
    click.echo(result.changes or "(none)")
