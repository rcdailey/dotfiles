"""Project milestone commands."""

from __future__ import annotations

import shlex

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Issue, Milestone
from linear_cli._queries import (
    ISSUE_CONNECTION,
    ISSUES_QUERY,
    MILESTONE_CREATE_MUTATION,
    MILESTONE_DELETE_MUTATION,
    MILESTONE_FIELDS,
    MILESTONE_UPDATE_MUTATION,
)
from linear_cli._render import echo_issue_summary, is_open, percentage_text, sort_issues
from linear_cli._resolve import Batch, project_filter, resolve_project_id

_ISSUE_PAGE = 250


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List, create, update, and delete project milestones."""


@cli.command("list")
@click.option("--project", required=True, help="Project name or UUID.")
def list_milestones(project: str) -> None:
    """List milestones for a project."""
    batch = Batch()
    get_project = batch.project_node(
        project, f"projectMilestones {{ nodes {{ {MILESTONE_FIELDS} }} }}"
    )
    batch.run()
    nodes = (get_project().get("projectMilestones") or {}).get("nodes", [])
    if not nodes:
        click.echo("no milestones found")
        return
    for node in nodes:
        m = Milestone.from_graphql(node)
        status = m.status or "unknown"
        date = m.target_date or "no date"
        pct = percentage_text(m.progress)
        click.echo(f"{m.name}  [{status}]  target: {date}  progress: {pct}")


@cli.command("view")
@click.argument("milestone_name")
@click.option("--project", required=True, help="Project name or UUID.")
@click.option("--limit", default=20, show_default=True, help="Maximum issues to show.")
@click.option("--all", "show_all", is_flag=True, help="Show every issue, ignoring --limit.")
def view_milestone(milestone_name: str, project: str, limit: int, show_all: bool) -> None:
    """View a milestone and its issues: open work first, newest update first."""
    batch = Batch()
    get_project = batch.project_id(project)
    get_milestone = batch.milestone(
        milestone_name,
        project_filter(project),
        f"{MILESTONE_FIELDS} issues(first: {_ISSUE_PAGE}) {{ {ISSUE_CONNECTION} }}",
    )
    batch.run()
    get_project()
    ms_node = get_milestone()
    m = Milestone.from_graphql(ms_node)
    pct = percentage_text(m.progress)
    click.echo(f"name:     {m.name}")
    click.echo(f"status:   {m.status or 'unknown'}")
    click.echo(f"target:   {m.target_date or 'no date'}")
    click.echo(f"progress: {pct}")
    if m.description:
        click.echo("")
        click.echo(m.description)

    issue_filt = {"projectMilestone": {"id": {"eq": ms_node["id"]}}}
    variables: dict = {"filter": issue_filt, "first": _ISSUE_PAGE}
    try:
        issue_nodes = paginate(
            ISSUES_QUERY, variables, ["issues"], first_page=ms_node.get("issues") or {}
        )
    except LinearError as exc:
        die(str(exc))

    click.echo("")
    if not issue_nodes:
        click.echo("no issues in this milestone")
        return
    issues = sort_issues([Issue.from_graphql(node) for node in issue_nodes])
    open_count = sum(1 for issue in issues if is_open(issue))
    click.echo(f"issues (open: {open_count}/{len(issues)}):")
    shown = issues if show_all else issues[:limit]
    for issue in shown:
        echo_issue_summary(issue, indent="  ")
    hidden = len(issues) - len(shown)
    if hidden > 0:
        args = f"{shlex.quote(milestone_name)} --project {shlex.quote(project)}"
        click.echo(f"  +{hidden} more: linear milestones view {args} --all")


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
    project_id = resolve_project_id(project)
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
