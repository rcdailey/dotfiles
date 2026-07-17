"""Project update commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import ProjectUpdate
from linear_cli._queries import PROJECT_UPDATE_CREATE_MUTATION, PROJECT_UPDATES_QUERY
from linear_cli._resolve import resolve_project_id

_HEALTH_CHOICES = ["onTrack", "atRisk", "offTrack"]
_PREVIEW_LEN = 200


@click.group("project-updates", cls=HelpfulGroup)
def cli() -> None:
    """List and create Linear project updates."""


@cli.command("list")
@click.argument("project_id_or_name")
def list_updates(project_id_or_name: str) -> None:
    """List project updates for a project (ID or name)."""
    project_id = _resolve_id(project_id_or_name)

    try:
        data = execute(PROJECT_UPDATES_QUERY, {"id": project_id, "first": 50})
    except LinearError as exc:
        die(str(exc))

    project = data.get("project") or {}
    nodes = (project.get("projectUpdates") or {}).get("nodes", [])
    if not nodes:
        click.echo("no project updates found")
        return

    for node in nodes:
        update = ProjectUpdate.from_graphql(node)
        preview = (update.body or "")[:_PREVIEW_LEN]
        if len(update.body or "") > _PREVIEW_LEN:
            preview += "..."
        click.echo(f"[{update.health}] {update.created_at} by {update.user_name}")
        if preview:
            click.echo(f"  {preview}")


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
    project_id = _resolve_id(project_id_or_name)

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


def _resolve_id(id_or_name: str) -> str:
    """Return UUID as-is (UUID pattern) or resolve by name."""
    # UUIDs contain hyphens and are 36 chars; names typically don't match that pattern.
    if len(id_or_name) == 36 and id_or_name.count("-") == 4:
        return id_or_name
    return resolve_project_id(id_or_name)
