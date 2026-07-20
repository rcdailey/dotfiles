"""Project milestone commands."""

from __future__ import annotations

import re

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Issue, Milestone, priority_label
from linear_cli._queries import (
    ISSUES_QUERY,
    MILESTONE_CREATE_MUTATION,
    MILESTONE_DELETE_MUTATION,
    MILESTONE_UPDATE_MUTATION,
    MILESTONES_QUERY,
)
from linear_cli._resolve import resolve_milestone_id, resolve_project_id

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
        pct = f"{m.progress:.0f}%" if m.progress is not None else "0%"
        click.echo(f"{m.name}  [{status}]  target: {date}  progress: {pct}")


@cli.command("view")
@click.argument("milestone_name")
@click.option("--project", required=True, help="Project name or UUID.")
def view_milestone(milestone_name: str, project: str) -> None:
    """View a milestone and its issues."""
    project_id = _to_project_id(project)
    milestone_id = resolve_milestone_id(milestone_name, project_id)

    filt = {"project": {"id": {"eq": project_id}}}
    try:
        ms_data = execute(MILESTONES_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (ms_data.get("projectMilestones") or {}).get("nodes", [])
    ms_node = next((n for n in nodes if n.get("id") == milestone_id), None)
    if not ms_node:
        die(f"milestone '{milestone_name}' not found")

    m = Milestone.from_graphql(ms_node)
    pct = f"{m.progress:.0f}%" if m.progress is not None else "0%"
    click.echo(f"name:     {m.name}")
    click.echo(f"status:   {m.status or 'unknown'}")
    click.echo(f"target:   {m.target_date or 'no date'}")
    click.echo(f"progress: {pct}")
    if m.description:
        click.echo("")
        click.echo(m.description)

    issue_filt = {"projectMilestone": {"id": {"eq": milestone_id}}}
    variables: dict = {"filter": issue_filt, "first": 250, "after": None}
    try:
        issue_nodes = paginate(ISSUES_QUERY, variables, ["issues"])
    except LinearError as exc:
        die(str(exc))

    if issue_nodes:
        click.echo("")
        click.echo(f"issues ({len(issue_nodes)}):")
        for node in issue_nodes:
            issue = Issue.from_graphql(node)
            pri = priority_label(issue.priority)
            labels = ", ".join(issue.labels) if issue.labels else ""
            parts = [f"  {issue.identifier}  {issue.state_name}  [{pri}]  {issue.title}"]
            if issue.assignee_name:
                parts.append(f"assignee: {issue.assignee_name}")
            if labels:
                parts.append(f"labels: {labels}")
            est = (
                "-"
                if issue.estimate is None
                else (
                    str(int(issue.estimate))
                    if issue.estimate == int(issue.estimate)
                    else str(issue.estimate)
                )
            )
            parts.append(f"estimate: {est}")
            click.echo("  ".join(parts))
    else:
        click.echo("")
        click.echo("no issues in this milestone")


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
