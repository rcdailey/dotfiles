"""Project commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Project
from linear_cli._queries import PROJECT_QUERY, PROJECTS_QUERY
from linear_cli._resolve import resolve_team_id


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List and view Linear projects."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Filter by team key (e.g. ENG).")
def list_projects(team_key: str | None) -> None:
    """List projects."""
    filt: dict | None = None
    if team_key:
        team_id = resolve_team_id(team_key)
        filt = {"accessibleTeams": {"id": {"eq": team_id}}}

    try:
        data = execute(PROJECTS_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("projects") or {}).get("nodes", [])
    if not nodes:
        click.echo("no projects found")
        return
    for node in nodes:
        proj = Project.from_graphql(node)
        dates = ""
        if proj.start_date or proj.target_date:
            dates = f"  {proj.start_date or '?'} -> {proj.target_date or '?'}"
        click.echo(f"{proj.name}  [{proj.state}]{dates}")


@cli.command("view")
@click.argument("id_or_name")
def view_project(id_or_name: str) -> None:
    """View project detail by ID or name."""
    node: dict | None = None

    # Try direct ID lookup first.
    try:
        data = execute(PROJECT_QUERY, {"id": id_or_name})
        node = data.get("project")
    except LinearError:
        node = None

    # Fall back to name search.
    if not node:
        try:
            list_data = execute(PROJECTS_QUERY, {"filter": None})
        except LinearError as exc:
            die(str(exc))
        all_nodes = (list_data.get("projects") or {}).get("nodes", [])
        for n in all_nodes:
            if (n.get("name") or "").lower() == id_or_name.lower():
                # Fetch full detail by ID.
                try:
                    detail_data = execute(PROJECT_QUERY, {"id": n["id"]})
                    node = detail_data.get("project")
                except LinearError as exc:
                    die(str(exc))
                break

    if not node:
        die(f"project '{id_or_name}' not found")

    proj = Project.from_graphql(node)
    click.echo(f"name:        {proj.name}")
    click.echo(f"state:       {proj.state}")
    click.echo(f"start:       {proj.start_date or 'not set'}")
    click.echo(f"target:      {proj.target_date or 'not set'}")
    click.echo(f"members:     {', '.join(proj.members) if proj.members else 'none'}")
    if proj.description:
        click.echo("")
        click.echo(proj.description)
    if proj.issues:
        click.echo("")
        click.echo("issues:")
        for issue in proj.issues:
            state_name = (issue.get("state") or {}).get("name", "")
            click.echo(f"  {issue.get('identifier')}  [{state_name}]  {issue.get('title')}")
