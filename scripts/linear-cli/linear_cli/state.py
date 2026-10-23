"""Workflow state listing commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import State
from linear_cli._queries import STATE_FIELDS, STATES_QUERY
from linear_cli._resolve import Batch


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Inspect Linear workflow states."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Team key (e.g. ENG).")
def list_states(team_key: str | None) -> None:
    """List workflow states, optionally filtered by team."""
    if team_key:
        batch = Batch()
        get_team = batch.team_node(team_key, f"states {{ nodes {{ {STATE_FIELDS} }} }}")
        batch.run()
        nodes = (get_team().get("states") or {}).get("nodes", [])
    else:
        try:
            data = execute(STATES_QUERY)
        except LinearError as exc:
            die(str(exc))
        nodes = (data.get("workflowStates") or {}).get("nodes", [])
    if not nodes:
        click.echo("no states found")
        return
    for node in sorted(nodes, key=lambda n: (n.get("type", ""), n.get("position", 0))):
        state = State.from_graphql(node)
        click.echo(f"{state.type:12}  {state.name:30}  ({state.id})")
