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
) -> dict:
    return {
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
