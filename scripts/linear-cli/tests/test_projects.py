"""Tests for the projects commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _project_node(
    proj_id: str = "proj-uuid-1",
    name: str = "Alpha",
    state: str = "started",
    start_date: str | None = "2026-01-01",
    target_date: str | None = "2026-06-01",
) -> dict:
    return {
        "id": proj_id,
        "name": name,
        "state": state,
        "startDate": start_date,
        "targetDate": target_date,
    }


def _project_detail_node(
    proj_id: str = "proj-uuid-1",
    name: str = "Alpha",
    state: str = "started",
    include_updates: bool = False,
    include_teams: bool = False,
) -> dict:
    node: dict = {
        "id": proj_id,
        "name": name,
        "state": state,
        "startDate": "2026-01-01",
        "targetDate": "2026-06-01",
        "description": "Main project",
        "members": {"nodes": [{"name": "Alice"}, {"name": "Bob"}]},
        "issues": {
            "nodes": [
                {"identifier": "ENG-1", "title": "First issue", "state": {"name": "In Progress"}},
            ]
        },
    }
    if include_teams:
        node["teams"] = {
            "nodes": [
                {
                    "key": "ENG",
                    "name": "Engineering",
                    "states": {
                        "nodes": [
                            {"name": "In Progress", "type": "started", "position": 1.0},
                            {"name": "Backlog", "type": "backlog", "position": 0.0},
                            {"name": "Done", "type": "completed", "position": 2.0},
                        ]
                    },
                },
            ]
        }
    if include_updates:
        node["projectUpdates"] = {
            "nodes": [
                {
                    "id": "upd-uuid-1",
                    "body": "Progress is good.",
                    "health": "onTrack",
                    "createdAt": "2026-07-10T09:00:00Z",
                    "user": {"name": "Alice"},
                },
                {
                    "id": "upd-uuid-2",
                    "body": "Blocked on design review.",
                    "health": "atRisk",
                    "createdAt": "2026-07-05T08:00:00Z",
                    "user": {"name": "Bob"},
                },
            ]
        }
    return node


def test_projects_list_shows_names():
    with patch(
        "linear_cli.projects.execute",
        return_value={"projects": {"nodes": [_project_node()]}},
    ):
        result = CliRunner().invoke(cli, ["projects", "list"])

    assert result.exit_code == 0
    assert "Alpha" in result.output
    assert "started" in result.output


def test_projects_list_empty():
    with patch(
        "linear_cli.projects.execute",
        return_value={"projects": {"nodes": []}},
    ):
        result = CliRunner().invoke(cli, ["projects", "list"])

    assert result.exit_code == 0
    assert "no projects found" in result.output


def test_projects_list_with_team():
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={
                "teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}
            },
        ),
        patch(
            "linear_cli.projects.execute",
            return_value={"projects": {"nodes": [_project_node()]}},
        ),
    ):
        result = CliRunner().invoke(cli, ["projects", "list", "--team", "ENG"])

    assert result.exit_code == 0
    assert "Alpha" in result.output


def test_projects_view_by_id():
    with patch(
        "linear_cli.projects.execute",
        return_value={"project": _project_detail_node()},
    ):
        result = CliRunner().invoke(cli, ["projects", "view", "proj-uuid-1"])

    assert result.exit_code == 0
    assert "Alpha" in result.output
    assert "Alice" in result.output
    assert "ENG-1" in result.output


def test_projects_view_shows_recent_updates():
    with patch(
        "linear_cli.projects.execute",
        return_value={"project": _project_detail_node(include_updates=True)},
    ):
        result = CliRunner().invoke(cli, ["projects", "view", "proj-uuid-1"])

    assert result.exit_code == 0
    assert "recent updates (2):" in result.output
    assert "onTrack" in result.output
    assert "Progress is good." in result.output
    assert "atRisk" in result.output
    assert "Blocked on design review." in result.output


def test_projects_view_no_updates_section_when_empty():
    with patch(
        "linear_cli.projects.execute",
        return_value={"project": _project_detail_node()},
    ):
        result = CliRunner().invoke(cli, ["projects", "view", "proj-uuid-1"])

    assert result.exit_code == 0
    assert "recent updates" not in result.output


def test_projects_view_shows_teams_and_states():
    with patch(
        "linear_cli.projects.execute",
        return_value={"project": _project_detail_node(include_teams=True)},
    ):
        result = CliRunner().invoke(cli, ["projects", "view", "proj-uuid-1"])

    assert result.exit_code == 0
    assert "teams:" in result.output
    assert "ENG  Engineering" in result.output
    assert "backlog" in result.output
    assert "Backlog" in result.output
    assert "started" in result.output
    assert "In Progress" in result.output
    assert "completed" in result.output
    assert "Done" in result.output


def test_projects_view_no_teams_section_when_empty():
    with patch(
        "linear_cli.projects.execute",
        return_value={"project": _project_detail_node()},
    ):
        result = CliRunner().invoke(cli, ["projects", "view", "proj-uuid-1"])

    assert result.exit_code == 0
    assert "teams:" not in result.output


def test_projects_view_by_name_fallback():
    list_response = {"projects": {"nodes": [_project_node()]}}
    detail_response = {"project": _project_detail_node()}

    with patch(
        "linear_cli.projects.execute",
        side_effect=[None, list_response, detail_response],
    ) as mock_exec:
        # First call raises LinearError (id not found), rest succeed via side_effect list
        from linear_cli._errors import LinearError

        mock_exec.side_effect = [LinearError("not found"), list_response, detail_response]
        result = CliRunner().invoke(cli, ["projects", "view", "Alpha"])

    assert result.exit_code == 0
    assert "Alpha" in result.output
