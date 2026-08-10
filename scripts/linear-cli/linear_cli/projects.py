"""Project commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Project, ProjectUpdate
from linear_cli._queries import PROJECT_QUERY, PROJECT_UPDATE_MUTATION, PROJECTS_QUERY
from linear_cli._render import percentage_text
from linear_cli._resolve import resolve_project_id, resolve_team_id


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
        nodes = paginate(
            PROJECTS_QUERY,
            {"filter": filt, "first": 50, "after": None},
            ["projects"],
        )
    except LinearError as exc:
        die(str(exc))

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
    try:
        project_id = resolve_project_id(id_or_name)
        data = execute(PROJECT_QUERY, {"id": project_id})
    except LinearError as exc:
        die(str(exc))
    node = data.get("project")

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
    if proj.teams:
        click.echo("")
        click.echo("teams:")
        for team in proj.teams:
            click.echo(f"  {team.get('key')}  {team.get('name')}")
            states = (team.get("states") or {}).get("nodes", [])
            for s in sorted(states, key=lambda s: (s.get("type", ""), s.get("position", 0))):
                click.echo(f"    {s.get('type', ''):12}  {s.get('name', '')}")
    if proj.issues:
        click.echo("")
        click.echo("issues:")
        for issue in proj.issues:
            state_name = (issue.get("state") or {}).get("name", "")
            click.echo(f"  {issue.get('identifier')}  [{state_name}]  {issue.get('title')}")
    if proj.milestones:
        click.echo("")
        click.echo("milestones:")
        for ms in proj.milestones:
            status = ms.get("status") or "unknown"
            date = ms.get("targetDate") or "no date"
            raw_progress = ms.get("progress")
            pct = percentage_text(raw_progress)
            click.echo(f"  {ms.get('name')}  [{status}]  target: {date}  progress: {pct}")
    if proj.project_updates:
        click.echo("")
        click.echo(f"recent updates ({len(proj.project_updates)}):")
        _preview_len = 200
        for node in proj.project_updates:
            update = ProjectUpdate.from_graphql(node)
            preview = (update.body or "")[:_preview_len]
            if len(update.body or "") > _preview_len:
                preview += "..."
            click.echo(f"  [{update.health}] {update.created_at} by {update.user_name}")
            if preview:
                click.echo(f"    {preview}")


@cli.command("update")
@click.argument("id_or_name")
@click.option("--name", default=None, help="New project name.")
@click.option("--description", default=None, help="New project description.")
def update_project(
    id_or_name: str,
    name: str | None,
    description: str | None,
) -> None:
    """Update a project by ID or name."""
    input_data: dict = {}
    if name:
        input_data["name"] = name
    if description is not None:
        input_data["description"] = description
    if not input_data:
        die("no updates specified")

    project_id = resolve_project_id(id_or_name)
    try:
        data = execute(
            PROJECT_UPDATE_MUTATION,
            {"id": project_id, "input": input_data},
        )
    except LinearError as exc:
        die(str(exc))
    result = data.get("projectUpdate") or {}
    if not result.get("success"):
        die("project update failed")
    project = result.get("project") or {}
    click.echo(f"updated project: {project.get('name', id_or_name)}")
