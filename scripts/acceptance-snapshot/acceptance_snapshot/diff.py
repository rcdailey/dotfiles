"""Show a targeted acceptance iteration diff."""

from __future__ import annotations

import click

from acceptance_snapshot._errors import SnapshotError
from acceptance_snapshot._state import pending_diff


@click.command()
@click.argument("paths", nargs=-1, required=True)
def cli(paths: tuple[str, ...]) -> None:
    """Show changes for one or more repository paths."""
    try:
        output = pending_diff(paths)
    except SnapshotError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1) from None
    click.echo(output, nl=not output.endswith("\n"))
