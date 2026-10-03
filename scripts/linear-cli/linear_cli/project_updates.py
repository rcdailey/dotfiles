"""Project update commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import ProjectUpdate
from linear_cli._queries import (
    PROJECT_UPDATE_CREATE_MUTATION,
    PROJECT_UPDATE_FIELDS,
    PROJECT_UPDATES_ALL_QUERY,
)
from linear_cli._render import echo_project_update
from linear_cli._resolve import Batch, resolve_project_id

_HEALTH_CHOICES = ["onTrack", "atRisk", "offTrack"]


@click.group("project-updates", cls=HelpfulGroup)
def cli() -> None:
    """List and create Linear project updates."""


@cli.command("list")
@click.argument("project_id_or_name", required=False, default=None)
@click.option("--full", is_flag=True, help="Show full update bodies instead of previews.")
def list_updates(project_id_or_name: str | None, full: bool) -> None:
    """List project updates. Omit project to list all recent workspace updates."""
    if project_id_or_name is None:
        try:
            data = execute(PROJECT_UPDATES_ALL_QUERY, {"first": 50})
        except LinearError as exc:
            die(str(exc))
        nodes = (data.get("projectUpdates") or {}).get("nodes", [])
    else:
        batch = Batch()
        get_project = batch.project_node(
            project_id_or_name,
            f"projectUpdates(first: 50, orderBy: createdAt) {{ nodes {{ {PROJECT_UPDATE_FIELDS} }} }}",
        )
        batch.run()
        nodes = (get_project().get("projectUpdates") or {}).get("nodes", [])

    if not nodes:
        click.echo("no project updates found")
        return

    for node in nodes:
        echo_project_update(ProjectUpdate.from_graphql(node), full=full)


@cli.command("add")
@click.argument("project_id_or_name")
@click.option("--body", required=True, help="Update body text.")
@click.option(
    "--health",
    default="onTrack",
    show_default=True,
    type=click.Choice(_HEALTH_CHOICES),
    help="Project health status.",
)
def add_update(project_id_or_name: str, body: str, health: str) -> None:
    """Create a project update."""
    project_id = resolve_project_id(project_id_or_name)

    try:
        data = execute(
            PROJECT_UPDATE_CREATE_MUTATION,
            {"input": {"projectId": project_id, "body": body, "health": health}},
        )
    except LinearError as exc:
        die(str(exc))

    result = data.get("projectUpdateCreate") or {}
    if not result.get("success"):
        die("project update creation failed")

    update = result.get("projectUpdate") or {}
    click.echo(f"created: {update.get('id')}")
    click.echo(f"health:  {update.get('health')}")
    click.echo(f"url:     {update.get('url')}")
