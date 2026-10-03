"""Issue management commands."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Comment, Issue, priority_label
from linear_cli._queries import (
    COMMENTS_QUERY,
    ISSUE_CONNECTION,
    ISSUE_HISTORY_QUERY,
    ISSUE_QUERY,
    ISSUE_SEARCH_QUERY,
    ISSUE_UPDATE_MUTATION,
    ISSUES_QUERY,
)
from linear_cli._render import echo_comments, echo_issue_summary, estimate_text
from linear_cli._resolve import Batch, project_filter, team_filter, user_filter
from linear_cli.relations import RELATION_TYPES, relation_input

_STATE_TYPES = ["triage", "backlog", "unstarted", "started", "completed", "canceled"]
_TIME_HELP = "ISO date/datetime or duration (e.g. 2026-09-20, -P1D = 1 day ago)."
_MAX_PAGE = 250


def _print_scope(project_name: str | None, milestone_name: str | None) -> None:
    """Print an explicit query scope when project filters are active."""
    if not project_name:
        return
    scope = f"scope: project {project_name}"
    if milestone_name:
        scope += f", milestone {milestone_name}"
    click.echo(scope)


@dataclass(frozen=True)
class _IssueQuery:
    """CLI filter options shared by `issues list` and `issues search`."""

    team_key: str | None
    state_type: str | None
    assignee: str | None
    creator: str | None
    label: str | None
    cycle: str | None
    estimate_filter: str | None
    project_name: str | None
    milestone_name: str | None
    created_after: str | None
    updated_after: str | None
    started_after: str | None
    completed_after: str | None
    limit: int


def _issue_filter(opts: _IssueQuery, batch: Batch) -> tuple[dict, list[Callable[[], Any]]]:
    """Translate CLI filters into one server-side IssueFilter.

    Names stay in the filter for Linear to match, so no lookup request precedes the issue query.
    Existence checks ride in ``batch`` alongside it; the returned getters die with the same
    not-found errors a separate lookup would raise.
    """
    if opts.cycle and not (opts.cycle.isdigit() or opts.cycle in ("active", "previous")):
        die(f"unknown cycle value '{opts.cycle}'; expected 'active', 'previous', or an integer")
    checks: list[Callable[[], Any]] = []
    issue_filter: dict = {}
    if opts.team_key:
        issue_filter["team"] = team_filter(opts.team_key)
        needs_active = opts.cycle in ("active", "previous")
        team = batch.team_node(opts.team_key, "id activeCycle { number }" if needs_active else "id")
        checks.append(team)
        if needs_active:
            checks.append(
                lambda: team().get("activeCycle") or die("no active cycle found for team")
            )
    if opts.state_type:
        issue_filter["state"] = {"type": {"eq": opts.state_type}}
    if opts.assignee:
        issue_filter["assignee"] = user_filter(opts.assignee)
    if opts.creator:
        issue_filter["creator"] = user_filter(opts.creator)
    if opts.label:
        issue_filter["labels"] = {"name": {"eq": opts.label}}
    if opts.cycle == "active":
        issue_filter["cycle"] = {"isActive": {"eq": True}}
    elif opts.cycle == "previous":
        issue_filter["cycle"] = {"isPrevious": {"eq": True}}
    elif opts.cycle:
        issue_filter["cycle"] = {"number": {"eq": int(opts.cycle)}}
    if opts.estimate_filter is not None:
        if opts.estimate_filter.lower() == "none":
            issue_filter["estimate"] = {"null": True}
        else:
            issue_filter["estimate"] = {"eq": float(opts.estimate_filter)}
    if opts.project_name:
        project = project_filter(opts.project_name)
        issue_filter["project"] = project
        checks.append(batch.project_id(opts.project_name))
        if opts.milestone_name and opts.milestone_name.lower() == "none":
            issue_filter["projectMilestone"] = {"null": True}
        elif opts.milestone_name:
            milestone = {"name": {"eqIgnoreCase": opts.milestone_name}}
            issue_filter["projectMilestone"] = milestone
            checks.append(batch.milestone(opts.milestone_name, project))
    # Linear's DateTimeOrDuration scalar parses and validates these values server-side.
    for key, value in (
        ("createdAt", opts.created_after),
        ("updatedAt", opts.updated_after),
        ("startedAt", opts.started_after),
        ("completedAt", opts.completed_after),
    ):
        if value:
            issue_filter[key] = {"gt": value}
    return issue_filter, checks


def _show_issues(opts: _IssueQuery, term: str | None) -> None:
    """Fetch the first page with filter checks in one request, page on, and render."""
    if opts.cycle and not opts.team_key:
        raise SystemExit("error: --cycle requires --team")
    if opts.milestone_name and not opts.project_name:
        raise SystemExit("error: --milestone requires --project")
    batch = Batch()
    issue_filter, checks = _issue_filter(opts, batch)
    variables: dict = {"filter": issue_filter or None, "first": min(opts.limit, _MAX_PAGE)}
    field_vars: dict[str, tuple[str, Any]] = {
        "filter": ("IssueFilter", variables["filter"]),
        "first": ("Int", variables["first"]),
    }
    if term is None:
        query, path = ISSUES_QUERY, "issues"
        field = f"issues(filter: $filter, first: $first) {{ {ISSUE_CONNECTION} }}"
    else:
        query, path = ISSUE_SEARCH_QUERY, "searchIssues"
        variables["term"] = term
        field_vars["term"] = ("String!", term)
        field = (
            f"searchIssues(term: $term, filter: $filter, first: $first) {{ {ISSUE_CONNECTION} }}"
        )
    alias = batch.add(field, field_vars)
    batch.run()
    for check in checks:
        check()
    try:
        nodes = paginate(
            query, variables, [path], limit=opts.limit, first_page=batch.data.get(alias) or {}
        )
    except LinearError as exc:
        die(str(exc))

    _print_scope(opts.project_name, opts.milestone_name)
    if not nodes:
        click.echo("no issues found")
        return
    for node in nodes:
        echo_issue_summary(Issue.from_graphql(node))


def _filter_options(func: Callable) -> Callable:
    """Attach the filter options shared by `issues list` and `issues search`."""
    options = [
        click.option("--team", "team_key", default=None, help="Team key (e.g. ENG)."),
        click.option(
            "--state",
            "state_type",
            default=None,
            type=click.Choice(_STATE_TYPES, case_sensitive=False),
            help="Filter by state type.",
        ),
        click.option("--assignee", default=None, help="Assignee user UUID or 'me'."),
        click.option("--creator", default=None, help="Creator user UUID or 'me'."),
        click.option("--label", default=None, help="Label name to filter by."),
        click.option(
            "--cycle", default=None, type=str, help="Cycle: 'active', 'previous', or number."
        ),
        click.option(
            "--estimate",
            "estimate_filter",
            default=None,
            type=str,
            help="Estimate: 'none' or a number.",
        ),
        click.option("--project", "project_name", default=None, help="Project name or UUID."),
        click.option(
            "--milestone",
            "milestone_name",
            default=None,
            help="Milestone name, or 'none' for issues outside milestones (requires --project).",
        ),
        click.option("--created-after", default=None, help=_TIME_HELP),
        click.option("--updated-after", default=None, help=_TIME_HELP),
        click.option("--started-after", default=None, help=_TIME_HELP),
        click.option("--completed-after", default=None, help=_TIME_HELP),
        click.option("--limit", default=50, show_default=True, help="Maximum number of issues."),
    ]
    for option in reversed(options):
        func = option(func)
    return func


def _history_actor(node: dict) -> str:
    """Name who made a history change; integrations appear as bots, automation as system."""
    if name := (node.get("actor") or {}).get("name"):
        return name
    if name := (node.get("botActor") or {}).get("name"):
        return f"{name} (bot)"
    return "system"


def _history_changes(node: dict) -> list[str]:
    """Describe each field a history event changed."""
    changes: list[str] = []

    def transition(label: str, key: str, attr: str | None = None, fmt=str) -> None:
        old, new = node.get(f"from{key}"), node.get(f"to{key}")
        if attr:
            old, new = (old or {}).get(attr), (new or {}).get(attr)
        if old is None and new is None:
            return
        old_text = "none" if old is None else fmt(old)
        new_text = "none" if new is None else fmt(new)
        changes.append(f"{label}: {old_text} -> {new_text}")

    transition("state", "State", "name")
    transition("assignee", "Assignee", "name")
    transition("priority", "Priority", fmt=lambda p: priority_label(int(p)))
    transition("estimate", "Estimate", fmt=estimate_text)
    transition("title", "Title")
    labels = [f"+{ln['name']}" for ln in node.get("addedLabels") or []]
    labels += [f"-{ln['name']}" for ln in node.get("removedLabels") or []]
    if labels:
        changes.append(f"labels: {' '.join(labels)}")
    transition("project", "Project", "name")
    transition("milestone", "ProjectMilestone", "name")
    transition("cycle", "Cycle", "number")
    transition("parent", "Parent", "identifier")
    transition("team", "Team", "key")
    transition("due", "DueDate")
    if node.get("updatedDescription"):
        changes.append("description edited")
    if attachment := node.get("attachment"):
        changes.append(f"linked: {attachment.get('title') or attachment.get('url')}")
    for relation in node.get("relationChanges") or []:
        changes.append(f"relation: {relation.get('type')} {relation.get('identifier')}")
    if (archived := node.get("archived")) is not None:
        changes.append("archived" if archived else "unarchived")
    if (trashed := node.get("trashed")) is not None:
        changes.append("trashed" if trashed else "restored")
    return changes or ["other change"]


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Create, list, view, and update Linear issues."""


@cli.command("list")
@_filter_options
def list_issues(**options: Any) -> None:
    """List issues with optional filters."""
    _show_issues(_IssueQuery(**options), None)


@cli.command("search")
@click.argument("query")
@_filter_options
def search(query: str, **options: Any) -> None:
    """Full-text search across issue titles, descriptions, and comments."""
    _show_issues(_IssueQuery(**options), query)


@cli.command("view")
@click.argument("issue_id")
@click.option("--comments", "include_comments", is_flag=True, help="Include issue comments.")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Print the Linear GraphQL issue node as JSON; --comments fills comments.nodes.",
)
def view(issue_id: str, include_comments: bool, as_json: bool) -> None:
    """View a single issue by ID or identifier (e.g. ENG-123)."""
    try:
        data = execute(ISSUE_QUERY, {"id": issue_id, "withComments": include_comments})
        node = data.get("issue")
        if not node:
            die(f"issue '{issue_id}' not found")
        comment_nodes: list[dict] = []
        if include_comments:
            comment_nodes = paginate(
                COMMENTS_QUERY,
                {"issueId": issue_id, "first": 100},
                ["issue", "comments"],
                first_page=node.get("commentThread") or {},
            )
            # Rename in place so --json keeps the key order of the comment-less shape.
            node = {
                ("comments" if key == "commentThread" else key): (
                    {"nodes": comment_nodes} if key == "commentThread" else value
                )
                for key, value in node.items()
            }
    except LinearError as exc:
        die(str(exc))

    if as_json:
        click.echo(json.dumps(node, indent=2))
        return

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
    if issue.project_name:
        project_state = f" ({issue.project_state})" if issue.project_state else ""
        click.echo(f"project:     {issue.project_name}{project_state}")
    if issue.milestone_name:
        click.echo(f"milestone:   {issue.milestone_name}")
    if issue.parent_identifier:
        click.echo(f"parent:      {issue.parent_identifier}  {issue.parent_title}")
    click.echo(f"url:         {issue.url}")
    click.echo(f"created:     {issue.created_at}")
    click.echo(f"started:     {issue.started_at or 'not started'}")
    click.echo(f"completed:   {issue.completed_at or 'not completed'}")
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
        click.echo("")
        if not comment_nodes:
            click.echo("no comments")
            return
        click.echo(f"comments ({len(comment_nodes)}):")
        echo_comments([Comment.from_graphql(node) for node in comment_nodes])


@cli.command("history")
@click.argument("issue_id")
def history(issue_id: str) -> None:
    """Show who changed what on an issue, oldest first."""
    try:
        nodes = paginate(ISSUE_HISTORY_QUERY, {"id": issue_id, "first": 100}, ["issue", "history"])
    except LinearError as exc:
        die(str(exc))

    if not nodes:
        click.echo("no history")
        return
    for node in sorted(nodes, key=lambda n: n.get("createdAt") or ""):
        changes = "; ".join(_history_changes(node))
        click.echo(f"{node.get('createdAt')}  {_history_actor(node)}  {changes}")


@cli.command("create")
@click.option("--title", required=True, help="Issue title.")
@click.option("--team", "team_key", required=True, help="Team key (e.g. ENG).")
@click.option("--description", default=None, help="Issue description (markdown).")
@click.option("--state", "state_name", default=None, help="State display name.")
@click.option("--priority", default=0, type=click.IntRange(0, 4), help="Priority (0-4).")
@click.option("--assignee", default=None, help="Assignee user UUID or 'me'.")
@click.option("--label", "label_names", multiple=True, help="Label name (repeatable).")
@click.option(
    "--parent", "parent_id", default=None, help="Parent issue identifier (e.g. ENG-123) or UUID."
)
@click.option("--estimate", default=None, type=float, help="Story point estimate.")
@click.option("--project", "project_name", default=None, help="Project name to assign.")
@click.option(
    "--milestone",
    "milestone_name",
    default=None,
    help="Milestone name; --project needed only if the name is ambiguous.",
)
@click.option(
    "--relation",
    "relations",
    multiple=True,
    type=(click.Choice(RELATION_TYPES, case_sensitive=False), str),
    metavar="TYPE ISSUE",
    help="Relation from the new issue, e.g. --relation blocked-by ENG-1 (repeatable).",
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
    relations: tuple[tuple[str, str], ...],
) -> None:
    """Create a new issue."""
    # One lookup request resolves every name and validates relation targets, so a typo fails
    # before the issue exists.
    batch = Batch()
    get_team = batch.team_id(team_key)
    get_state = batch.state_id(state_name, team_filter(team_key)) if state_name else None
    get_assignee = batch.user_id(assignee) if assignee else None
    label_getters = [batch.label_id(name) for name in label_names]
    get_parent = batch.issue(parent_id) if parent_id else None
    relation_getters = [(rel_type, batch.issue(ref), ref) for rel_type, ref in relations]
    get_project = batch.project_id(project_name) if project_name else None
    get_milestone = (
        batch.milestone(milestone_name, project_filter(project_name))
        if project_name and milestone_name
        else None
    )
    get_scope = (
        batch.milestone_scope(milestone_name) if milestone_name and not project_name else None
    )
    batch.run()

    # The issue ID is chosen here so relations can join the creation mutation document.
    issue_id = str(uuid.uuid4())
    input_data: dict = {"id": issue_id, "title": title, "teamId": get_team(), "priority": priority}
    if description:
        input_data["description"] = description
    if get_state:
        input_data["stateId"] = get_state()
    if get_assignee:
        input_data["assigneeId"] = get_assignee()
    if label_getters:
        input_data["labelIds"] = [get() for get in label_getters]
    if get_parent:
        input_data["parentId"] = get_parent()["id"]
    if estimate is not None:
        input_data["estimate"] = estimate
    if get_project:
        input_data["projectId"] = get_project()
    if get_milestone:
        input_data["projectMilestoneId"] = get_milestone()["id"]
    if get_scope:
        input_data["projectId"], input_data["projectMilestoneId"] = get_scope()

    targets = [(rel_type, get()["id"], ref) for rel_type, get, ref in relation_getters]
    decls = ["$input: IssueCreateInput!"]
    fields = ["issueCreate(input: $input) { success issue { id identifier title url } }"]
    variables: dict = {"input": input_data}
    for index, (rel_type, related_id, _) in enumerate(targets):
        decls.append(f"$r{index}: IssueRelationCreateInput!")
        fields.append(f"r{index}: issueRelationCreate(input: $r{index}) {{ success }}")
        variables[f"r{index}"] = relation_input(issue_id, rel_type, related_id)
    # Fields run in order, so relations see the created issue. Linear applies a mutation document
    # atomically: if any relation fails, the issue is not created either.
    mutation = f"mutation({', '.join(decls)}) {{\n  " + "\n  ".join(fields) + "\n}"
    try:
        data = execute(mutation, variables)
    except LinearError as exc:
        die(str(exc))
    results = [data.get("issueCreate")] + [data.get(f"r{i}") for i in range(len(targets))]
    if not all((result or {}).get("success") for result in results):
        die("issue creation failed")

    issue = (data.get("issueCreate") or {}).get("issue") or {}
    click.echo(f"created {issue.get('identifier')}  {issue.get('title')}")
    click.echo(issue.get("url"))
    for rel_type, _, related_ref in targets:
        click.echo(f"relation created: {rel_type}  {related_ref}")


@cli.command("update")
@click.argument("issue_ids", nargs=-1, required=True)
@click.option("--title", default=None, help="New title.")
@click.option("--description", default=None, help="New description (markdown).")
@click.option("--state", "state_name", default=None, help="New state display name.")
@click.option("--priority", default=None, type=click.IntRange(0, 4), help="New priority (0-4).")
@click.option("--assignee", default=None, help="Assignee user UUID, 'me', or 'none' to unassign.")
@click.option("--add-label", "add_labels", multiple=True, help="Label name to add (repeatable).")
@click.option(
    "--remove-label", "remove_labels", multiple=True, help="Label name to remove (repeatable)."
)
@click.option("--estimate", default=None, type=float, help="Story point estimate.")
@click.option(
    "--parent", "parent_id", default=None, help="Parent issue identifier (e.g. ENG-123) or UUID."
)
@click.option("--project", "project_name", default=None, help="Project name to assign.")
@click.option(
    "--milestone",
    "milestone_name",
    default=None,
    help="Milestone name; resolved within the issue's project, --project, or the workspace.",
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
        _update_many(issue_ids, project_name, milestone_name)
        return

    issue_ref = issue_ids[0]
    batch = Batch()
    # State and milestone names resolve through the issue's own team and project, nested in the
    # same lookup request, so the issue is never fetched on its own.
    issue_fields = ["id"]
    issue_vars: dict[str, tuple[str, Any]] = {"id": ("String!", issue_ref)}
    if state_name:
        issue_fields.append("team { states(filter: $states) { nodes { id } } }")
        issue_vars["states"] = ("WorkflowStateFilter", {"name": {"eqIgnoreCase": state_name}})
    if milestone_name and not project_name:
        issue_fields.append(
            "project { id projectMilestones(filter: $milestones) { nodes { id } } }"
        )
        issue_vars["milestones"] = (
            "ProjectMilestoneFilter",
            {"name": {"eqIgnoreCase": milestone_name}},
        )
    issue_alias = (
        batch.add(f"issue(id: $id) {{ {' '.join(issue_fields)} }}", issue_vars)
        if len(issue_fields) > 1
        else None
    )
    assign_me = assignee is not None and assignee.lower() == "me"
    get_viewer = batch.user_id(assignee) if assign_me else None
    add_getters = [batch.label_id(name) for name in add_labels]
    remove_getters = [batch.label_id(name) for name in remove_labels]
    get_parent = batch.issue(parent_id) if parent_id else None
    get_project = batch.project_id(project_name) if project_name else None
    get_milestone = (
        batch.milestone(milestone_name, project_filter(project_name))
        if project_name and milestone_name
        else None
    )
    get_scope = (
        batch.milestone_scope(milestone_name) if milestone_name and not project_name else None
    )

    input_data: dict = {}
    if title:
        input_data["title"] = title
    if description is not None:
        input_data["description"] = description
    if priority is not None:
        input_data["priority"] = priority
    if assignee is not None and not assign_me:
        input_data["assigneeId"] = None if assignee.lower() == "none" else assignee
    if estimate is not None:
        input_data["estimate"] = estimate
    if not input_data and not batch:
        die("no updates specified")

    batch.run()
    issue_node = batch.data.get(issue_alias) or {} if issue_alias else {}
    if state_name:
        states = ((issue_node.get("team") or {}).get("states") or {}).get("nodes", [])
        if not states:
            die(f"state '{state_name}' not found")
        input_data["stateId"] = states[0]["id"]
    if get_viewer:
        input_data["assigneeId"] = get_viewer()
    # Delta fields leave labels this command does not name untouched.
    removed = [get() for get in remove_getters]
    added = [label_id for label_id in (get() for get in add_getters) if label_id not in removed]
    if added:
        input_data["addedLabelIds"] = added
    if removed:
        input_data["removedLabelIds"] = removed
    if get_parent:
        input_data["parentId"] = get_parent()["id"]
    if get_project:
        input_data["projectId"] = get_project()
    if get_milestone:
        input_data["projectMilestoneId"] = get_milestone()["id"]
    if get_scope:
        project = issue_node.get("project")
        if project:
            milestones = (project.get("projectMilestones") or {}).get("nodes", [])
            if not milestones:
                die(f"milestone '{milestone_name}' not found in project")
            input_data["projectMilestoneId"] = milestones[0]["id"]
        else:
            input_data["projectId"], input_data["projectMilestoneId"] = get_scope()

    try:
        issue = _update_issue(issue_ref, input_data)
    except LinearError as exc:
        die(str(exc))
    click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")


def _update_issue(issue_ref: str, input_data: dict) -> dict:
    """Apply one issue update and return the updated issue node."""
    data = execute(ISSUE_UPDATE_MUTATION, {"id": issue_ref, "input": input_data})
    result = data.get("issueUpdate") or {}
    if not result.get("success"):
        raise LinearError("issue update failed")
    return result.get("issue") or {}


def _update_many(
    issue_refs: tuple[str, ...], project_name: str, milestone_name: str | None
) -> None:
    """Move several issues to a project and milestone with one lookup and one mutation request.

    Linear applies a mutation document atomically, so one bad reference rejects every aliased
    update. Only then does each issue get its own request, so valid issues still move and each
    failure is reported separately.
    """
    batch = Batch()
    get_project = batch.project_id(project_name)
    get_milestone = (
        batch.milestone(milestone_name, project_filter(project_name)) if milestone_name else None
    )
    batch.run()
    update_input: dict = {"projectId": get_project()}
    if get_milestone:
        update_input["projectMilestoneId"] = get_milestone()["id"]

    decls = ["$input: IssueUpdateInput!"]
    fields = []
    variables: dict = {"input": update_input}
    for index, ref in enumerate(issue_refs):
        decls.append(f"$i{index}: String!")
        fields.append(
            f"u{index}: issueUpdate(id: $i{index}, input: $input) "
            "{ success issue { identifier title } }"
        )
        variables[f"i{index}"] = ref
    mutation = f"mutation({', '.join(decls)}) {{\n  " + "\n  ".join(fields) + "\n}"
    try:
        data = execute(mutation, variables)
    except LinearError:
        data = {}
    results = [data.get(f"u{index}") or {} for index in range(len(issue_refs))]
    if results and all(result.get("success") for result in results):
        for result in results:
            issue = result.get("issue") or {}
            click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")
        return

    failed = False
    for ref in issue_refs:
        try:
            issue = _update_issue(ref, update_input)
        except LinearError as exc:
            click.echo(f"error: {ref}: {exc}", err=True)
            failed = True
            continue
        click.echo(f"updated {issue.get('identifier')}  {issue.get('title')}")
    if failed:
        raise SystemExit(1)
