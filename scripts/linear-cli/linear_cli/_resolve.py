"""Resolve human-readable identifiers to Linear UUIDs."""

from __future__ import annotations

import re

from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._queries import (
    LABELS_QUERY,
    MILESTONES_QUERY,
    PROJECTS_QUERY,
    STATES_QUERY,
    TEAM_ACTIVE_CYCLE_QUERY,
    TEAMS_QUERY,
    VIEWER_QUERY,
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


def _query_nodes(query: str, variables: dict | None, connection: str) -> list[dict]:
    """Execute a resolver query and return its connection nodes."""
    try:
        data = execute(query, variables)
    except LinearError as exc:
        die(str(exc))
    return (data.get(connection) or {}).get("nodes", [])


def resolve_team_id(team_key: str) -> str:
    """Resolve a team key (e.g. ENG) to its UUID."""
    nodes = _query_nodes(TEAMS_QUERY, None, "teams")
    for node in nodes:
        if node.get("key", "").upper() == team_key.upper():
            return node["id"]
    die(f"team '{team_key}' not found")


def resolve_state_id(state_name: str, team_id: str | None) -> str:
    """Resolve a state display name to its UUID."""
    filt = {"team": {"id": {"eq": team_id}}} if team_id else None
    nodes = _query_nodes(STATES_QUERY, {"filter": filt}, "workflowStates")
    for node in nodes:
        if node.get("name", "").lower() == state_name.lower():
            return node["id"]
    die(f"state '{state_name}' not found")


def resolve_label_id(label_name: str) -> str:
    """Resolve a label name to its UUID.

    Filters by exact name server-side to avoid pagination issues with large
    label sets. Labels are workspace-scoped; no team filter applied.
    """
    filt = {"name": {"eqIgnoreCase": label_name}}
    nodes = _query_nodes(LABELS_QUERY, {"filter": filt}, "issueLabels")
    if nodes:
        return nodes[0]["id"]
    die(f"label '{label_name}' not found")


def resolve_project_id(project_name: str) -> str:
    """Resolve a project name to its UUID."""
    if _UUID_RE.match(project_name):
        return project_name
    filt = {"name": {"eqIgnoreCase": project_name}}
    nodes = _query_nodes(
        PROJECTS_QUERY,
        {"filter": filt, "first": 2},
        "projects",
    )
    for node in nodes:
        if node.get("name", "").casefold() == project_name.casefold():
            return node["id"]
    die(f"project '{project_name}' not found")


def resolve_milestone_id(milestone_name: str, project_id: str) -> str:
    """Resolve a milestone name to its UUID within a project."""
    return resolve_milestone(milestone_name, project_id)["id"]


def resolve_milestone(milestone_name: str, project_id: str) -> dict:
    """Resolve a milestone name to its GraphQL node within a project."""
    filt = {
        "project": {"id": {"eq": project_id}},
        "name": {"eqIgnoreCase": milestone_name},
    }
    nodes = _query_nodes(
        MILESTONES_QUERY,
        {"filter": filt},
        "projectMilestones",
    )
    for node in nodes:
        if (node.get("name") or "").lower() == milestone_name.lower():
            return node
    die(f"milestone '{milestone_name}' not found in project")


def resolve_cycle_number(cycle: str, team_id: str | None) -> int:
    """Resolve 'active', 'previous', or a digit string to a cycle number."""
    if cycle.isdigit():
        return int(cycle)
    if not team_id:
        die("error: --cycle requires --team")
    try:
        data = execute(TEAM_ACTIVE_CYCLE_QUERY, {"id": team_id})
    except LinearError as exc:
        die(str(exc))
    active_cycle = (data.get("team") or {}).get("activeCycle")
    if not active_cycle:
        die("no active cycle found for team")
    number: int = int(active_cycle["number"])
    if cycle == "active":
        return number
    if cycle == "previous":
        return number - 1
    die(f"unknown cycle value '{cycle}'; expected 'active', 'previous', or an integer")


def resolve_assignee_id(assignee: str) -> str:
    """Resolve assignee 'me' or pass through UUID."""
    if assignee.lower() == "me":
        try:
            data = execute(VIEWER_QUERY)
        except LinearError as exc:
            die(str(exc))
        viewer = data.get("viewer") or {}
        uid = viewer.get("id")
        if not uid:
            die("could not resolve viewer id")
        return uid
    return assignee
