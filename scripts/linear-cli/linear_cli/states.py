"""Workflow state listing commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import State
from linear_cli._queries import STATES_QUERY
from linear_cli._resolve import resolve_team_id


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Inspect Linear workflow states."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Team key (e.g. ENG).")
def list_states(team_key: str | None) -> None:
    """List workflow states, optionally filtered by team."""
    team_id = resolve_team_id(team_key) if team_key else None
    filt: dict | None = None
    if team_id:
        filt = {"team": {"id": {"eq": team_id}}}
    try:
        data = execute(STATES_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("workflowStates") or {}).get("nodes", [])
    if not nodes:
        click.echo("no states found")
        return
    for node in sorted(nodes, key=lambda n: (n.get("type", ""), n.get("position", 0))):
        state = State.from_graphql(node)
        click.echo(f"{state.type:12}  {state.name:30}  ({state.id})")
