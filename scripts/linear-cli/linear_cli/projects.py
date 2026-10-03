"""Project commands."""

from __future__ import annotations

import shlex

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Issue, Project, ProjectUpdate
from linear_cli._queries import (
    PROJECT_CREATE_MUTATION,
    PROJECT_FIELDS,
    PROJECT_ISSUES_QUERY,
    PROJECT_UPDATE_MUTATION,
    PROJECTS_QUERY,
)
from linear_cli._render import (
    echo_project_update,
    is_open,
    issue_times_text,
    percentage_text,
    sort_issues,
)
from linear_cli._resolve import Batch, resolve_project_id, team_filter

_PROJECT_PAGE = "pageInfo { hasNextPage endCursor } nodes { id name state startDate targetDate }"
_ISSUE_PAGE = 250
# Open issues shown per milestone; the rest sit behind a printed drill-down command so the
# overview stays small without hiding that anything was cut.
_GROUP_LIMIT = 20


def _echo_issue_group(header: str, issues: list[Issue], drill_down: str, *, gap: bool) -> None:
    """Print one milestone heading with its open/total count and top open issues."""
    open_issues = sort_issues([issue for issue in issues if is_open(issue)])
    if gap:
        click.echo("")
    click.echo(f"  {header}  open: {len(open_issues)}/{len(issues)}")
    for issue in open_issues[:_GROUP_LIMIT]:
        click.echo(
            f"    {issue.identifier}  [{issue.state_name}]  {issue.title}  "
            f"{issue_times_text(issue)}"
        )
    hidden = len(open_issues) - _GROUP_LIMIT
    if hidden > 0:
        click.echo(f"    +{hidden} more: {drill_down}")


def _echo_milestone_groups(proj: Project, issue_nodes: list[dict]) -> None:
    """Print each milestone with its issues, then issues outside any milestone."""
    by_milestone: dict[str | None, list[Issue]] = {}
    for node in issue_nodes:
        milestone_id = (node.get("projectMilestone") or {}).get("id")
        by_milestone.setdefault(milestone_id, []).append(Issue.from_graphql(node))
    if not proj.milestones and not by_milestone:
        return

    project_arg = shlex.quote(proj.name or proj.id or "")
    click.echo("")
    click.echo("milestones:")
    for index, ms in enumerate(proj.milestones):
        status = ms.get("status") or "unknown"
        date = ms.get("targetDate") or "no date"
        pct = percentage_text(ms.get("progress"))
        name = ms.get("name") or ""
        _echo_issue_group(
            f"{name}  [{status}]  target: {date}  progress: {pct}",
            by_milestone.pop(ms.get("id"), []),
            f"linear milestones view {shlex.quote(name)} --project {project_arg} --all",
            gap=index > 0,
        )
    unassigned = [issue for issues in by_milestone.values() for issue in issues]
    if unassigned:
        _echo_issue_group(
            "no milestone",
            unassigned,
            f"linear issues list --project {project_arg} --milestone none --limit {len(unassigned)}",
            gap=bool(proj.milestones),
        )


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List, view, create, and update Linear projects."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Filter by team key (e.g. ENG).")
def list_projects(team_key: str | None) -> None:
    """List projects."""
    variables: dict = {"filter": None, "first": 50}
    first_page = None
    if team_key:
        variables["filter"] = {"accessibleTeams": {"some": team_filter(team_key)}}
        batch = Batch()
        get_team = batch.team_id(team_key)
        alias = batch.add(
            f"projects(filter: $filter, first: $first) {{ {_PROJECT_PAGE} }}",
            {"filter": ("ProjectFilter", variables["filter"]), "first": ("Int", 50)},
        )
        batch.run()
        get_team()
        first_page = batch.data.get(alias) or {}

    try:
        nodes = paginate(PROJECTS_QUERY, variables, ["projects"], first_page=first_page)
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
@click.option("--full", is_flag=True, help="Show full project update bodies instead of previews.")
def view_project(id_or_name: str, full: bool) -> None:
    """View project detail by ID or name."""
    batch = Batch()
    get_project = batch.project_node(id_or_name, PROJECT_FIELDS)
    batch.run()
    proj = Project.from_graphql(get_project())
    click.echo(f"name:        {proj.name}")
    click.echo(f"id:          {proj.id}")
    click.echo(f"url:         {proj.url}")
    click.echo(f"state:       {proj.state}")
    click.echo(f"start:       {proj.start_date or 'not set'}")
    click.echo(f"target:      {proj.target_date or 'not set'}")
    click.echo(f"members:     {', '.join(proj.members) if proj.members else 'none'}")
    click.echo(f"description: {proj.description or 'none'}")
    if proj.external_links:
        click.echo("")
        click.echo("links:")
        for link in proj.external_links:
            click.echo(f"  {link.get('label')}  {link.get('url')}")
    if proj.content:
        click.echo("")
        click.echo(proj.content)
    if proj.teams:
        click.echo("")
        click.echo("teams:")
        for team in proj.teams:
            click.echo(f"  {team.get('key')}  {team.get('name')}")
            states = (team.get("states") or {}).get("nodes", [])
            for s in sorted(states, key=lambda s: (s.get("type", ""), s.get("position", 0))):
                click.echo(f"    {s.get('type', ''):12}  {s.get('name', '')}")
    try:
        issue_nodes = paginate(
            PROJECT_ISSUES_QUERY,
            {"id": proj.id, "first": _ISSUE_PAGE},
            ["project", "issues"],
            first_page=proj.issues_page,
        )
    except LinearError as exc:
        die(str(exc))
    _echo_milestone_groups(proj, issue_nodes)
    if proj.project_updates:
        click.echo("")
        click.echo(f"recent updates ({len(proj.project_updates)}):")
        for update_node in proj.project_updates:
            echo_project_update(ProjectUpdate.from_graphql(update_node), full=full, indent="  ")


@cli.command("create")
@click.option("--name", required=True, help="Project name.")
@click.option(
    "--team", "team_keys", required=True, multiple=True, help="Team key (repeatable, e.g. ENG)."
)
@click.option("--description", default=None, help="Project description (markdown).")
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--target-date", default=None, help="Target date (YYYY-MM-DD).")
def create_project(
    name: str,
    team_keys: tuple[str, ...],
    description: str | None,
    start_date: str | None,
    target_date: str | None,
) -> None:
    """Create a project."""
    batch = Batch()
    team_getters = [batch.team_id(key) for key in team_keys]
    batch.run()
    input_data: dict = {"name": name, "teamIds": [get() for get in team_getters]}
    if description:
        input_data["description"] = description
    if start_date:
        input_data["startDate"] = start_date
    if target_date:
        input_data["targetDate"] = target_date

    try:
        data = execute(PROJECT_CREATE_MUTATION, {"input": input_data})
    except LinearError as exc:
        die(str(exc))
    result = data.get("projectCreate") or {}
    if not result.get("success"):
        die("project creation failed")
    project = result.get("project") or {}
    click.echo(f"created project: {project.get('name', name)}")
    click.echo(project.get("url"))


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
