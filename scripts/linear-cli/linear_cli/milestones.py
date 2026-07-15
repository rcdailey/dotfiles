"""Project milestone commands."""

from __future__ import annotations

import re

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Milestone
from linear_cli._queries import (
    MILESTONE_CREATE_MUTATION,
    MILESTONE_DELETE_MUTATION,
    MILESTONE_UPDATE_MUTATION,
    MILESTONES_QUERY,
)
from linear_cli._resolve import resolve_project_id

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _to_project_id(project: str) -> str:
    """Return UUID directly if already one, else resolve by name."""
    if _UUID_RE.match(project):
        return project
    return resolve_project_id(project)


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List, create, update, and delete project milestones."""


@cli.command("list")
@click.option("--project", required=True, help="Project name or UUID.")
def list_milestones(project: str) -> None:
    """List milestones for a project."""
    project_id = _to_project_id(project)
    filt = {"project": {"id": {"eq": project_id}}}
    try:
        data = execute(MILESTONES_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("projectMilestones") or {}).get("nodes", [])
    if not nodes:
        click.echo("no milestones found")
        return
    for node in nodes:
        m = Milestone.from_graphql(node)
        status = m.status or "unknown"
        date = m.target_date or "no date"
        pct = f"{m.progress * 100:.0f}%" if m.progress is not None else "0%"
        click.echo(f"{m.name}  [{status}]  target: {date}  progress: {pct}")


@cli.command("create")
@click.option("--project", required=True, help="Project name or UUID.")
@click.option("--name", required=True, help="Milestone name.")
@click.option("--description", default=None, help="Optional description.")
@click.option("--target-date", default=None, help="Target date (YYYY-MM-DD).")
def create_milestone(
    project: str,
    name: str,
    description: str | None,
    target_date: str | None,
) -> None:
    """Create a milestone in a project."""
    project_id = _to_project_id(project)
    inp: dict = {"name": name, "projectId": project_id}
    if description:
        inp["description"] = description
    if target_date:
        inp["targetDate"] = target_date

    try:
        data = execute(MILESTONE_CREATE_MUTATION, {"input": inp})
    except LinearError as exc:
        die(str(exc))

    result = data.get("projectMilestoneCreate") or {}
    if not result.get("success"):
        die("milestone creation failed")

    ms = result.get("projectMilestone") or {}
    click.echo(f"milestone created: {ms.get('name', name)}")


@cli.command("update")
@click.argument("milestone_id")
@click.option("--name", default=None, help="New name.")
@click.option("--description", default=None, help="New description.")
@click.option("--target-date", default=None, help="New target date (YYYY-MM-DD).")
def update_milestone(
    milestone_id: str,
    name: str | None,
    description: str | None,
    target_date: str | None,
) -> None:
    """Update a milestone by ID."""
    inp: dict = {}
    if name:
        inp["name"] = name
    if description:
        inp["description"] = description
    if target_date:
        inp["targetDate"] = target_date

    if not inp:
        die("no update fields provided")

    try:
        data = execute(MILESTONE_UPDATE_MUTATION, {"id": milestone_id, "input": inp})
    except LinearError as exc:
        die(str(exc))

    result = data.get("projectMilestoneUpdate") or {}
    if not result.get("success"):
        die("milestone update failed")

    ms = result.get("projectMilestone") or {}
    click.echo(f"milestone updated: {ms.get('name', milestone_id)}")


@cli.command("delete")
@click.argument("milestone_id")
def delete_milestone(milestone_id: str) -> None:
    """Delete a milestone by ID."""
    try:
        data = execute(MILESTONE_DELETE_MUTATION, {"id": milestone_id})
    except LinearError as exc:
        die(str(exc))

    result = data.get("projectMilestoneDelete") or {}
    if not result.get("success"):
        die("milestone deletion failed")

    click.echo(f"milestone deleted: {milestone_id}")
