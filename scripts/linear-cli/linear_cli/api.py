"""Raw GraphQL passthrough for ad-hoc queries and mutations."""

from __future__ import annotations

import json
import sys

import click

from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute


@click.command()
@click.argument("query")
@click.option(
    "--var",
    "variables",
    multiple=True,
    help="Variable as key=value (repeatable). Values are parsed as JSON if possible.",
)
def cli(query: str, variables: tuple[str, ...]) -> None:
    """Execute a raw GraphQL query or mutation.

    QUERY is the GraphQL string. Pass variables with --var key=value.

    \b
    Examples:
      linear api 'query { viewer { id name } }'
      linear api 'query($id: String!) { issue(id: $id) { title } }' --var id=ENG-123
    """
    parsed_vars: dict = {}
    for v in variables:
        if "=" not in v:
            die(f"invalid variable format '{v}'; expected key=value")
        key, raw = v.split("=", 1)
        try:
            parsed_vars[key] = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            parsed_vars[key] = raw

    if query == "-":
        query = sys.stdin.read()

    try:
        data = execute(query, parsed_vars or None)
    except LinearError as exc:
        die(str(exc))

    click.echo(json.dumps(data, indent=2))
