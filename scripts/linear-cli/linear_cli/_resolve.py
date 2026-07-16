"""Resolve human-readable identifiers to Linear UUIDs."""

from __future__ import annotations

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


def resolve_team_id(team_key: str) -> str:
    """Resolve a team key (e.g. ENG) to its UUID."""
    try:
        data = execute(TEAMS_QUERY)
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("teams") or {}).get("nodes", [])
    for node in nodes:
        if node.get("key", "").upper() == team_key.upper():
            return node["id"]
    die(f"team '{team_key}' not found")


def resolve_state_id(state_name: str, team_id: str | None) -> str:
    """Resolve a state display name to its UUID."""
    try:
        filt = {"team": {"id": {"eq": team_id}}} if team_id else None
        data = execute(STATES_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("workflowStates") or {}).get("nodes", [])
    for node in nodes:
        if node.get("name", "").lower() == state_name.lower():
            return node["id"]
    die(f"state '{state_name}' not found")


def resolve_label_id(label_name: str) -> str:
    """Resolve a label name to its UUID.

    Filters by exact name server-side to avoid pagination issues with large
    label sets. Labels are workspace-scoped; no team filter applied.
    """
    try:
        filt = {"name": {"eqIgnoreCase": label_name}}
        data = execute(LABELS_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("issueLabels") or {}).get("nodes", [])
    if nodes:
        return nodes[0]["id"]
    die(f"label '{label_name}' not found")


def resolve_project_id(project_name: str) -> str:
    """Resolve a project name to its UUID."""
    try:
        data = execute(PROJECTS_QUERY, {"filter": None})
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("projects") or {}).get("nodes", [])
    for node in nodes:
        if node.get("name", "").lower() == project_name.lower():
            return node["id"]
    die(f"project '{project_name}' not found")


def resolve_milestone_id(milestone_name: str, project_id: str) -> str:
    """Resolve a milestone name to its UUID within a project."""
    try:
        filt = {"project": {"id": {"eq": project_id}}}
        data = execute(MILESTONES_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("projectMilestones") or {}).get("nodes", [])
    for node in nodes:
        if (node.get("name") or "").lower() == milestone_name.lower():
            return node["id"]
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
