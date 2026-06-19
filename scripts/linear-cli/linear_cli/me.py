"""Show the authenticated user's profile."""

from __future__ import annotations

import click

from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import User
from linear_cli._queries import VIEWER_QUERY


@click.command()
def cli() -> None:
    """Print the authenticated user's info."""
    try:
        data = execute(VIEWER_QUERY)
    except LinearError as exc:
        die(str(exc))

    user = User.from_graphql(data.get("viewer", {}))
    click.echo(f"id:           {user.id}")
    click.echo(f"name:         {user.name}")
    click.echo(f"display name: {user.display_name}")
    click.echo(f"email:        {user.email}")
    click.echo(f"active:       {user.active}")
