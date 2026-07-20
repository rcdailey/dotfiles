"""Tests for the milestones commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli

_PROJ_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _milestone_node(
    ms_id: str = "ms-uuid-1",
    name: str = "Beta Launch",
    status: str = "inProgress",
    target_date: str | None = "2026-06-01",
    progress: float = 50.0,
) -> dict:
    return {
        "id": ms_id,
        "name": name,
        "description": "Ship the beta",
        "targetDate": target_date,
        "status": status,
        "progress": progress,
        "project": {"id": "proj-uuid-1", "name": "Alpha"},
    }


def _projects_response(proj_id: str = "proj-uuid-1", name: str = "Alpha") -> dict:
    return {
        "projects": {
            "nodes": [
                {
                    "id": proj_id,
                    "name": name,
                    "state": "started",
                    "startDate": None,
                    "targetDate": None,
                }
            ]
        }
    }


def test_milestones_list_by_name():
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.milestones.execute",
            return_value={"projectMilestones": {"nodes": [_milestone_node()]}},
        ),
    ):
        result = CliRunner().invoke(cli, ["milestones", "list", "--project", "Alpha"])

    assert result.exit_code == 0
    assert "Beta Launch" in result.output
    assert "inProgress" in result.output
    assert "50%" in result.output
    assert "2026-06-01" in result.output


def test_milestones_list_by_uuid():
    with patch(
        "linear_cli.milestones.execute",
        return_value={"projectMilestones": {"nodes": [_milestone_node()]}},
    ):
        result = CliRunner().invoke(cli, ["milestones", "list", "--project", _PROJ_UUID])

    assert result.exit_code == 0
    assert "Beta Launch" in result.output


def test_milestones_list_empty():
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.milestones.execute",
            return_value={"projectMilestones": {"nodes": []}},
        ),
    ):
        result = CliRunner().invoke(cli, ["milestones", "list", "--project", "Alpha"])

    assert result.exit_code == 0
    assert "no milestones found" in result.output


def test_milestones_list_no_date():
    node = _milestone_node(target_date=None, progress=0.0)
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.milestones.execute",
            return_value={"projectMilestones": {"nodes": [node]}},
        ),
    ):
        result = CliRunner().invoke(cli, ["milestones", "list", "--project", "Alpha"])

    assert result.exit_code == 0
    assert "no date" in result.output
    assert "0%" in result.output


def test_milestones_create_by_name():
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.milestones.execute",
            return_value={
                "projectMilestoneCreate": {
                    "success": True,
                    "projectMilestone": {"id": "ms-uuid-2", "name": "Beta Launch"},
                }
            },
        ),
    ):
        result = CliRunner().invoke(
            cli, ["milestones", "create", "--project", "Alpha", "--name", "Beta Launch"]
        )

    assert result.exit_code == 0
    assert "milestone created" in result.output
    assert "Beta Launch" in result.output


def test_milestones_create_with_options():
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.milestones.execute",
            return_value={
                "projectMilestoneCreate": {
                    "success": True,
                    "projectMilestone": {"id": "ms-uuid-3", "name": "v2"},
                }
            },
        ),
    ):
        result = CliRunner().invoke(
            cli,
            [
                "milestones",
                "create",
                "--project",
                "Alpha",
                "--name",
                "v2",
                "--description",
                "Second version",
                "--target-date",
                "2026-09-01",
            ],
        )

    assert result.exit_code == 0
    assert "milestone created" in result.output


def test_milestones_update_name():
    with patch(
        "linear_cli.milestones.execute",
        return_value={
            "projectMilestoneUpdate": {
                "success": True,
                "projectMilestone": {"id": "ms-uuid-1", "name": "Renamed"},
            }
        },
    ):
        result = CliRunner().invoke(cli, ["milestones", "update", "ms-uuid-1", "--name", "Renamed"])

    assert result.exit_code == 0
    assert "milestone updated" in result.output
    assert "Renamed" in result.output


def test_milestones_update_no_fields():
    result = CliRunner().invoke(cli, ["milestones", "update", "ms-uuid-1"])
    assert result.exit_code != 0


def test_milestones_delete():
    with patch(
        "linear_cli.milestones.execute",
        return_value={"projectMilestoneDelete": {"success": True}},
    ):
        result = CliRunner().invoke(cli, ["milestones", "delete", "ms-uuid-1"])

    assert result.exit_code == 0
    assert "milestone deleted" in result.output
    assert "ms-uuid-1" in result.output


def _issue_node(
    identifier: str = "ENG-1",
    title: str = "Fix the thing",
    state_name: str = "In Progress",
    priority: int = 2,
) -> dict:
    return {
        "id": "issue-uuid-1",
        "identifier": identifier,
        "title": title,
        "description": None,
        "priority": priority,
        "estimate": None,
        "url": "https://linear.app/team/issue/ENG-1",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "state": {"name": state_name, "type": "started"},
        "assignee": None,
        "labels": {"nodes": []},
        "parent": None,
        "children": {"nodes": []},
        "comments": {"nodes": []},
    }


def _milestones_response(ms_id: str = "ms-uuid-1") -> dict:
    return {"projectMilestones": {"nodes": [_milestone_node(ms_id=ms_id)]}}


def test_milestones_view_shows_details():
    # _resolve.execute: projects (name→id), then milestones (resolve_milestone_id)
    # milestones.execute: milestones (view_milestone body)
    with (
        patch(
            "linear_cli._resolve.execute",
            side_effect=[_projects_response(), _milestones_response()],
        ),
        patch("linear_cli.milestones.execute", return_value=_milestones_response()),
        patch("linear_cli.milestones.paginate", return_value=[_issue_node()]),
    ):
        result = CliRunner().invoke(
            cli, ["milestones", "view", "Beta Launch", "--project", "Alpha"]
        )

    assert result.exit_code == 0, result.output
    assert "Beta Launch" in result.output
    assert "inProgress" in result.output
    assert "50%" in result.output
    assert "2026-06-01" in result.output
    assert "Ship the beta" in result.output
    assert "ENG-1" in result.output
    assert "Fix the thing" in result.output


def test_milestones_view_no_issues():
    with (
        patch(
            "linear_cli._resolve.execute",
            side_effect=[_projects_response(), _milestones_response()],
        ),
        patch("linear_cli.milestones.execute", return_value=_milestones_response()),
        patch("linear_cli.milestones.paginate", return_value=[]),
    ):
        result = CliRunner().invoke(
            cli, ["milestones", "view", "Beta Launch", "--project", "Alpha"]
        )

    assert result.exit_code == 0, result.output
    assert "no issues in this milestone" in result.output
