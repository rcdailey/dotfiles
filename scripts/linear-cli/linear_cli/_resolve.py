"""Resolve human-readable identifiers to Linear UUIDs."""

from __future__ import annotations

from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._queries import (
    LABELS_QUERY,
    PROJECTS_QUERY,
    STATES_QUERY,
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


def resolve_label_id(label_name: str, team_id: str | None) -> str:
    """Resolve a label name to its UUID."""
    try:
        filt = {"team": {"id": {"eq": team_id}}} if team_id else None
        data = execute(LABELS_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))
    nodes = (data.get("issueLabels") or {}).get("nodes", [])
    for node in nodes:
        if node.get("name", "").lower() == label_name.lower():
            return node["id"]
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
