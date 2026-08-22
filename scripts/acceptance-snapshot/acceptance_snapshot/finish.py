"""Finish an acceptance snapshot iteration."""

from __future__ import annotations

import click

from acceptance_snapshot._errors import SnapshotError
from acceptance_snapshot._state import finish


@click.command()
def cli() -> None:
    """Promote the audited tree and detect concurrent changes."""
    try:
        result = finish()
    except SnapshotError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1) from None
    click.echo(f"Iteration: {result.iteration}")
    click.echo(f"Audited tree: {result.audited_tree}")
    click.echo(f"Current tree: {result.current_tree}")
    if result.stable:
        click.echo("Result: stable")
        return
    click.echo("Result: retry")
    click.echo("Changes since capture:")
    click.echo(result.changes or "(none)")
