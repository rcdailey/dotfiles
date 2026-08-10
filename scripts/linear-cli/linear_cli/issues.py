"""Issue management commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Comment, Issue, priority_label
from linear_cli._queries import (
    COMMENTS_QUERY,
    ISSUE_CREATE_MUTATION,
    ISSUE_QUERY,
    ISSUE_SEARCH_QUERY,
    ISSUE_UPDATE_MUTATION,
    ISSUES_QUERY,
)
from linear_cli._resolve import (
    resolve_assignee_id,
    resolve_cycle_number,
    resolve_label_id,
    resolve_milestone_id,
    resolve_project_id,
    resolve_state_id,
    resolve_team_id,
)
from linear_cli._render import echo_comment, echo_issue_summary, estimate_text


def _print_scope(project_name: str | None, milestone_name: str | None) -> None:
    """Print an explicit query scope when project filters are active."""
    if not project_name:
        return
    scope = f"scope: project {project_name}"
    if milestone_name:
        scope += f", milestone {milestone_name}"
    click.echo(scope)


def _build_issue_filter(
    team_key: str | None,
    state_type: str | None,
    assignee: str | None,
    label: str | None,
    cycle: str | None,
    estimate_filter: str | None,
    project_name: str | None,
    milestone_name: str | None,
) -> dict:
    """Resolve CLI filter values into one Linear IssueFilter."""
    team_id = resolve_team_id(team_key) if team_key else None
    assignee_id = resolve_assignee_id(assignee) if assignee else None
    issue_filter: dict = {}
    if team_id:
        issue_filter["team"] = {"id": {"eq": team_id}}
    if state_type:
        issue_filter["state"] = {"type": {"eq": state_type}}
    if assignee_id:
        issue_filter["assignee"] = {"id": {"eq": assignee_id}}
    if label:
        issue_filter["labels"] = {"name": {"eq": label}}
    if cycle:
        cycle_number = resolve_cycle_number(cycle, team_id)
        issue_filter["cycle"] = {"number": {"eq": cycle_number}}
    if estimate_filter is not None:
        if estimate_filter.lower() == "none":
            issue_filter["estimate"] = {"null": True}
        else:
            issue_filter["estimate"] = {"eq": float(estimate_filter)}

    project_id = resolve_project_id(project_name) if project_name else None
    if project_id:
        issue_filter["project"] = {"id": {"eq": project_id}}
    if milestone_name and project_id:
        milestone_id = resolve_milestone_id(milestone_name, project_id)
        issue_filter["projectMilestone"] = {"id": {"eq": milestone_id}}
    return issue_filter


def _show_issues(
    query: str,
    variables: dict,
    connection_path: list[str],
    limit: int,
    project_name: str | None,
    milestone_name: str | None,
) -> None:
    """Fetch and render one bounded issue result set."""
    try:
        nodes = paginate(
            query,
            variables,
            connection_path,
            limit=limit,
        )
    except LinearError as exc:
        die(str(exc))

    _print_scope(project_name, milestone_name)
    if not nodes:
        click.echo("no issues found")
        return
    for node in nodes:
        echo_issue_summary(Issue.from_graphql(node))


def _update_issue(issue_id: str, input_data: dict) -> dict:
    """Apply one issue update and return the updated issue node."""
    data = execute(ISSUE_UPDATE_MUTATION, {"id": issue_id, "input": input_data})
    result = data.get("issueUpdate") or {}
    if not result.get("success"):
        raise LinearError("issue update failed")
    return result.get("issue") or {}


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
@click.option("--cycle", default=None, type=str, help="Cycle: 'active', 'previous', or number.")
@click.option(
    "--estimate", "estimate_filter", default=None, type=str, help="Estimate: 'none' or a number."
)
@click.option("--project", "project_name", default=None, help="Project name or UUID.")
@click.option(
    "--milestone", "milestone_name", default=None, help="Milestone name (requires --project)."
)
@click.option("--limit", default=50, show_default=True, help="Maximum number of issues.")
def list_issues(
    team_key: str | None,
    state_type: str | None,
    assignee: str | None,
    label: str | None,
    cycle: str | None,
    estimate_filter: str | None,
    project_name: str | None,
    milestone_name: str | None,
    limit: int,
) -> None:
    """List issues with optional filters."""
    if cycle and not team_key:
        raise SystemExit("error: --cycle requires --team")
    if milestone_name and not project_name:
        raise SystemExit("error: --milestone requires --project")
    issue_filter = _build_issue_filter(
        team_key,
        state_type,
        assignee,
        label,
        cycle,
        estimate_filter,
        project_name,
        milestone_name,
    )
    variables: dict = {
        "filter": issue_filter or None,
        "first": min(limit, 250),
        "after": None,
    }
    _show_issues(
        ISSUES_QUERY,
        variables,
        ["issues"],
        limit,
        project_name,
        milestone_name,
    )


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
@click.option("--cycle", default=None, type=str, help="Cycle: 'active', 'previous', or number.")
@click.option(
    "--estimate", "estimate_filter", default=None, type=str, help="Estimate: 'none' or a number."
)
@click.option("--project", "project_name", default=None, help="Project name or UUID.")
@click.option(
    "--milestone", "milestone_name", default=None, help="Milestone name (requires --project)."
)
@click.option("--limit", default=50, show_default=True, help="Maximum number of issues.")
def search(
    query: str,
    team_key: str | None,
    state_type: str | None,
    assignee: str | None,
    label: str | None,
    cycle: str | None,
    estimate_filter: str | None,
    project_name: str | None,
    milestone_name: str | None,
    limit: int,
) -> None:
    """Full-text search across issue titles, descriptions, and comments."""
    if cycle and not team_key:
        raise SystemExit("error: --cycle requires --team")
    if milestone_name and not project_name:
        raise SystemExit("error: --milestone requires --project")
    issue_filter = _build_issue_filter(
        team_key,
        state_type,
        assignee,
        label,
        cycle,
        estimate_filter,
        project_name,
        milestone_name,
    )
    variables: dict = {
        "term": query,
        "filter": issue_filter or None,
        "first": min(limit, 250),
        "after": None,
    }
    _show_issues(
        ISSUE_SEARCH_QUERY,
        variables,
        ["searchIssues"],
        limit,
        project_name,
        milestone_name,
    )


@cli.command("view")
@click.argument("issue_id")
@click.option("--comments", "include_comments", is_flag=True, help="Include issue comments.")
def view(issue_id: str, include_comments: bool) -> None:
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
    click.echo(f"estimate:    {estimate_text(issue.estimate)}")
    click.echo(f"comments:    {issue.comment_count}")
    if issue.parent_identifier:
        click.echo(f"parent:      {issue.parent_identifier}  {issue.parent_title}")
    click.echo(f"url:         {issue.url}")
    click.echo(f"created:     {issue.created_at}")
    click.echo(f"updated:     {issue.updated_at}")
    if issue.children:
        click.echo("")
        click.echo(f"sub-issues ({len(issue.children)}):")
        for child in issue.children:
            echo_issue_summary(Issue.from_graphql(child), indent="  ")
    if issue.description:
        click.echo("")
        click.echo(issue.description)
    if include_comments:
        try:
            comment_nodes = paginate(
                COMMENTS_QUERY,
                {"issueId": issue_id, "first": 100},
                ["issue", "comments"],
            )
        except LinearError as exc:
            die(str(exc))
        click.echo("")
        if not comment_nodes:
            click.echo("no comments")
            return
        click.echo(f"comments ({len(comment_nodes)}):")
        for node in comment_nodes:
            echo_comment(Comment.from_graphql(node))


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
@click.option(
    "--milestone", "milestone_name", default=None, help="Milestone name (requires --project)."
)
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
    milestone_name: str | None,
) -> None:
    """Create a new issue."""
    if milestone_name and not project_name:
        die("--milestone requires --project")

    team_id = resolve_team_id(team_key)
    input_data: dict = {"title": title, "teamId": team_id, "priority": priority}

    if description:
        input_data["description"] = description
    if state_name:
        input_data["stateId"] = resolve_state_id(state_name, team_id)
    if assignee:
        input_data["assigneeId"] = resolve_assignee_id(assignee)
    if label_names:
        input_data["labelIds"] = [resolve_label_id(ln) for ln in label_names]
    if parent_id:
        input_data["parentId"] = parent_id
    if estimate is not None:
        input_data["estimate"] = estimate
    if project_name:
        project_id = resolve_project_id(project_name)
        input_data["projectId"] = project_id
        if milestone_name:
            input_data["projectMilestoneId"] = resolve_milestone_id(milestone_name, project_id)

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
@click.argument("issue_ids", nargs=-1, required=True)
@click.option("--title", default=None, help="New title.")
@click.option("--description", default=None, help="New description (markdown).")
@click.option("--state", "state_name", default=None, help="New state display name.")
@click.option("--priority", default=None, type=click.IntRange(0, 4), help="New priority (0-4).")
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--add-label", "add_labels", multiple=True, help="Label name to add (repeatable).")
@click.option(
    "--remove-label", "remove_labels", multiple=True, help="Label name to remove (repeatable)."
)
@click.option("--estimate", default=None, type=float, help="Story point estimate.")
@click.option("--parent", "parent_id", default=None, help="Parent issue ID or identifier.")
@click.option("--project", "project_name", default=None, help="Project name to assign.")
@click.option(
    "--milestone", "milestone_name", default=None, help="Milestone name within the issue's project."
)
def update(
    issue_ids: tuple[str, ...],
    title: str | None,
    description: str | None,
    state_name: str | None,
    priority: int | None,
    assignee: str | None,
    add_labels: tuple[str, ...],
    remove_labels: tuple[str, ...],
    estimate: float | None,
    parent_id: str | None,
    project_name: str | None,
    milestone_name: str | None,
) -> None:
    """Update an existing issue."""
    if len(issue_ids) > 1:
        unsupported_batch_fields = any(
            (
                title is not None,
                description is not None,
                state_name is not None,
                priority is not None,
                assignee is not None,
                add_labels,
                remove_labels,
                estimate is not None,
                parent_id is not None,
            )
        )
        if unsupported_batch_fields or not project_name:
            raise click.UsageError(
                "multiple issues require --project and support only --project/--milestone"
            )
        project_id = resolve_project_id(project_name)
        batch_input: dict = {"projectId": project_id}
        if milestone_name:
            batch_input["projectMilestoneId"] = resolve_milestone_id(
                milestone_name,
                project_id,
            )
        failed = False
        for batch_issue_id in issue_ids:
            try:
                issue = _update_issue(batch_issue_id, batch_input)
            except LinearError as exc:
                click.echo(f"error: {batch_issue_id}: {exc}", err=True)
                failed = True
                continue
            click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")
        if failed:
            raise SystemExit(1)
        return

    issue_id = issue_ids[0]
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
    if description is not None:
        input_data["description"] = description
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
                lid = resolve_label_id(ln)
                current_ids.add(lid)
        if remove_labels:
            for ln in remove_labels:
                lid = resolve_label_id(ln)
                current_ids.discard(lid)

        input_data["labelIds"] = list(current_ids)

    if estimate is not None:
        input_data["estimate"] = estimate
    if parent_id:
        input_data["parentId"] = parent_id
    if project_name:
        project_id = resolve_project_id(project_name)
        input_data["projectId"] = project_id
        if milestone_name:
            input_data["projectMilestoneId"] = resolve_milestone_id(milestone_name, project_id)
    elif milestone_name:
        project_data = node.get("project") or {}
        project_id = project_data.get("id")
        if not project_id:
            die("--milestone requires the issue to be in a project (or pass --project)")
        input_data["projectMilestoneId"] = resolve_milestone_id(milestone_name, project_id)

    if not input_data:
        die("no updates specified")

    try:
        issue = _update_issue(issue_id, input_data)
    except LinearError as exc:
        die(str(exc))
    click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")
