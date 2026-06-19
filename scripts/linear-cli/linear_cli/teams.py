"""Team listing and member commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Team, User
from linear_cli._queries import TEAM_MEMBERS_QUERY, TEAMS_QUERY
from linear_cli._resolve import resolve_team_id


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Manage and inspect Linear teams."""


@cli.command("list")
def list_teams() -> None:
    """List all teams."""
    try:
        data = execute(TEAMS_QUERY)
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("teams") or {}).get("nodes", [])
    if not nodes:
        click.echo("no teams found")
        return
    for node in nodes:
        team = Team.from_graphql(node)
        click.echo(f"{team.key}  {team.name}  ({team.id})")


@cli.command("members")
@click.argument("team_key")
def members(team_key: str) -> None:
    """List members of a team (accepts team key, e.g. ENG)."""
    team_id = resolve_team_id(team_key)
    try:
        data = execute(TEAM_MEMBERS_QUERY, {"teamId": team_id})
    except LinearError as exc:
        die(str(exc))

    nodes = ((data.get("team") or {}).get("members") or {}).get("nodes", [])
    if not nodes:
        click.echo("no members found")
        return
    for node in nodes:
        user = User.from_graphql(node)
        status = "active" if user.active else "inactive"
        click.echo(f"{user.name} <{user.email}>  [{status}]  ({user.id})")
