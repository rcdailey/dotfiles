"""Issue management commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Issue, priority_label
from linear_cli._queries import (
    ISSUE_CREATE_MUTATION,
    ISSUE_QUERY,
    ISSUE_SEARCH_QUERY,
    ISSUE_UPDATE_MUTATION,
    ISSUES_QUERY,
)
from linear_cli._resolve import (
    resolve_assignee_id,
    resolve_label_id,
    resolve_project_id,
    resolve_state_id,
    resolve_team_id,
)


def _print_issue(issue: Issue) -> None:
    """Print a single issue summary line."""
    pri = priority_label(issue.priority)
    labels = ", ".join(issue.labels) if issue.labels else ""
    parts = [f"{issue.identifier}  {issue.state_name}  [{pri}]  {issue.title}"]
    if issue.assignee_name:
        parts.append(f"assignee: {issue.assignee_name}")
    if labels:
        parts.append(f"labels: {labels}")
    click.echo("  ".join(parts))


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Create, list, view, and update Linear issues."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Team key (e.g. ENG).")
@click.option(
    "--state",
    "state_type",
    default=None,
    type=click.Choice(
        ["triage", "backlog", "unstarted", "started", "completed", "canceled"],
        case_sensitive=False,
    ),
    help="Filter by state type.",
)
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--label", default=None, help="Label name to filter by.")
@click.option("--limit", default=50, show_default=True, help="Maximum number of issues.")
def list_issues(
    team_key: str | None,
    state_type: str | None,
    assignee: str | None,
    label: str | None,
    limit: int,
) -> None:
    """List issues with optional filters."""
    team_id = resolve_team_id(team_key) if team_key else None
    assignee_id = resolve_assignee_id(assignee) if assignee else None

    filt: dict = {}
    if team_id:
        filt["team"] = {"id": {"eq": team_id}}
    if state_type:
        filt["state"] = {"type": {"eq": state_type}}
    if assignee_id:
        filt["assignee"] = {"id": {"eq": assignee_id}}
    if label:
        filt["labels"] = {"name": {"eq": label}}

    variables: dict = {
        "filter": filt or None,
        "first": min(limit, 250),
        "after": None,
    }
    try:
        nodes = paginate(ISSUES_QUERY, variables, ["issues"])
    except LinearError as exc:
        die(str(exc))

    nodes = nodes[:limit]
    if not nodes:
        click.echo("no issues found")
        return
    for node in nodes:
        _print_issue(Issue.from_graphql(node))


@cli.command("search")
@click.argument("query")
@click.option("--team", "team_key", default=None, help="Team key (e.g. ENG).")
@click.option(
    "--state",
    "state_type",
    default=None,
    type=click.Choice(
        ["triage", "backlog", "unstarted", "started", "completed", "canceled"],
        case_sensitive=False,
    ),
    help="Filter by state type.",
)
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--label", default=None, help="Label name to filter by.")
@click.option("--limit", default=50, show_default=True, help="Maximum number of issues.")
def search(
    query: str,
    team_key: str | None,
    state_type: str | None,
    assignee: str | None,
    label: str | None,
    limit: int,
) -> None:
    """Full-text search across issue titles, descriptions, and comments."""
    team_id = resolve_team_id(team_key) if team_key else None
    assignee_id = resolve_assignee_id(assignee) if assignee else None

    filt: dict = {}
    if team_id:
        filt["team"] = {"id": {"eq": team_id}}
    if state_type:
        filt["state"] = {"type": {"eq": state_type}}
    if assignee_id:
        filt["assignee"] = {"id": {"eq": assignee_id}}
    if label:
        filt["labels"] = {"name": {"eq": label}}

    variables: dict = {
        "term": query,
        "filter": filt or None,
        "first": min(limit, 250),
        "after": None,
    }
    try:
        nodes = paginate(ISSUE_SEARCH_QUERY, variables, ["searchIssues"])
    except LinearError as exc:
        die(str(exc))

    nodes = nodes[:limit]
    if not nodes:
        click.echo("no issues found")
        return
    for node in nodes:
        _print_issue(Issue.from_graphql(node))


@cli.command("view")
@click.argument("issue_id")
def view(issue_id: str) -> None:
    """View a single issue by ID or identifier (e.g. ENG-123)."""
    try:
        data = execute(ISSUE_QUERY, {"id": issue_id})
    except LinearError as exc:
        die(str(exc))

    node = data.get("issue")
    if not node:
        die(f"issue '{issue_id}' not found")

    issue = Issue.from_graphql(node)
    pri = priority_label(issue.priority)
    click.echo(f"identifier:  {issue.identifier}")
    click.echo(f"title:       {issue.title}")
    click.echo(f"state:       {issue.state_name} ({issue.state_type})")
    click.echo(f"priority:    {pri}")
    click.echo(f"assignee:    {issue.assignee_name or 'unassigned'}")
    click.echo(f"labels:      {', '.join(issue.labels) if issue.labels else 'none'}")
    click.echo(f"url:         {issue.url}")
    click.echo(f"created:     {issue.created_at}")
    click.echo(f"updated:     {issue.updated_at}")
    if issue.description:
        click.echo("")
        click.echo(issue.description)


@cli.command("create")
@click.option("--title", required=True, help="Issue title.")
@click.option("--team", "team_key", required=True, help="Team key (e.g. ENG).")
@click.option("--description", default=None, help="Issue description (markdown).")
@click.option("--state", "state_name", default=None, help="State display name.")
@click.option("--priority", default=0, type=click.IntRange(0, 4), help="Priority (0-4).")
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--label", "label_names", multiple=True, help="Label name (repeatable).")
@click.option("--parent", "parent_id", default=None, help="Parent issue UUID.")
@click.option("--estimate", default=None, type=float, help="Story point estimate.")
@click.option("--project", "project_name", default=None, help="Project name to assign.")
def create(
    title: str,
    team_key: str,
    description: str | None,
    state_name: str | None,
    priority: int,
    assignee: str | None,
    label_names: tuple[str, ...],
    parent_id: str | None,
    estimate: float | None,
    project_name: str | None,
) -> None:
    """Create a new issue."""
    team_id = resolve_team_id(team_key)
    input_data: dict = {"title": title, "teamId": team_id, "priority": priority}

    if description:
        input_data["description"] = description
    if state_name:
        input_data["stateId"] = resolve_state_id(state_name, team_id)
    if assignee:
        input_data["assigneeId"] = resolve_assignee_id(assignee)
    if label_names:
        input_data["labelIds"] = [resolve_label_id(ln, team_id) for ln in label_names]
    if parent_id:
        input_data["parentId"] = parent_id
    if estimate is not None:
        input_data["estimate"] = estimate
    if project_name:
        input_data["projectId"] = resolve_project_id(project_name)

    try:
        data = execute(ISSUE_CREATE_MUTATION, {"input": input_data})
    except LinearError as exc:
        die(str(exc))

    result = data.get("issueCreate") or {}
    if not result.get("success"):
        die("issue creation failed")

    issue = result.get("issue") or {}
    click.echo(f"created {issue.get('identifier')}  {issue.get('title')}")
    click.echo(issue.get("url"))


@cli.command("update")
@click.argument("issue_id")
@click.option("--title", default=None, help="New title.")
@click.option("--state", "state_name", default=None, help="New state display name.")
@click.option("--priority", default=None, type=click.IntRange(0, 4), help="New priority (0-4).")
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--add-label", "add_labels", multiple=True, help="Label name to add (repeatable).")
@click.option(
    "--remove-label", "remove_labels", multiple=True, help="Label name to remove (repeatable)."
)
@click.option("--estimate", default=None, type=float, help="Story point estimate.")
@click.option("--project", "project_name", default=None, help="Project name to assign.")
def update(
    issue_id: str,
    title: str | None,
    state_name: str | None,
    priority: int | None,
    assignee: str | None,
    add_labels: tuple[str, ...],
    remove_labels: tuple[str, ...],
    estimate: float | None,
    project_name: str | None,
) -> None:
    """Update an existing issue."""
    # Fetch current issue to get team context for label/state resolution.
    try:
        current_data = execute(ISSUE_QUERY, {"id": issue_id})
    except LinearError as exc:
        die(str(exc))

    node = current_data.get("issue")
    if not node:
        die(f"issue '{issue_id}' not found")

    team_data = node.get("team") or {}
    team_id: str | None = team_data.get("id")

    input_data: dict = {}
    if title:
        input_data["title"] = title
    if state_name:
        input_data["stateId"] = resolve_state_id(state_name, team_id)
    if priority is not None:
        input_data["priority"] = priority
    if assignee:
        input_data["assigneeId"] = resolve_assignee_id(assignee)

    if add_labels or remove_labels:
        current_label_nodes: list[dict] = (node.get("labels") or {}).get("nodes", [])
        current_ids: set[str] = {ln["id"] for ln in current_label_nodes if ln.get("id")}

        if add_labels:
            for ln in add_labels:
                lid = resolve_label_id(ln, team_id)
                current_ids.add(lid)
        if remove_labels:
            for ln in remove_labels:
                lid = resolve_label_id(ln, team_id)
                current_ids.discard(lid)

        input_data["labelIds"] = list(current_ids)

    if estimate is not None:
        input_data["estimate"] = estimate
    if project_name:
        input_data["projectId"] = resolve_project_id(project_name)

    if not input_data:
        die("no updates specified")

    try:
        data = execute(ISSUE_UPDATE_MUTATION, {"id": issue_id, "input": input_data})
    except LinearError as exc:
        die(str(exc))

    result = data.get("issueUpdate") or {}
    if not result.get("success"):
        die("issue update failed")

    issue = result.get("issue") or {}
    click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")
