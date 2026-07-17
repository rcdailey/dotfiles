"""Tests for the project-updates commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli

_PROJ_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _update_node(
    update_id: str = "upd-uuid-1",
    body: str = "Things are going well.",
    health: str = "onTrack",
    created_at: str = "2026-07-01T10:00:00Z",
    user_name: str = "Alice",
    project_name: str | None = None,
) -> dict:
    node: dict = {
        "id": update_id,
        "body": body,
        "health": health,
        "createdAt": created_at,
        "user": {"name": user_name},
    }
    if project_name is not None:
        node["project"] = {"name": project_name}
    return node


def _project_updates_response(nodes: list) -> dict:
    return {
        "project": {
            "projectUpdates": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": nodes,
            }
        }
    }


def _projects_response(proj_id: str = _PROJ_UUID, name: str = "Alpha") -> dict:
    return {"projects": {"nodes": [{"id": proj_id, "name": name, "state": "started"}]}}


def test_list_updates_shows_health_and_user():
    with (
        patch(
            "linear_cli.project_updates.execute",
            return_value=_project_updates_response([_update_node()]),
        ),
    ):
        result = CliRunner().invoke(cli, ["project-updates", "list", _PROJ_UUID])

    assert result.exit_code == 0
    assert "onTrack" in result.output
    assert "Alice" in result.output
    assert "Things are going well." in result.output


def test_list_updates_empty():
    with patch(
        "linear_cli.project_updates.execute",
        return_value=_project_updates_response([]),
    ):
        result = CliRunner().invoke(cli, ["project-updates", "list", _PROJ_UUID])

    assert result.exit_code == 0
    assert "no project updates found" in result.output


def test_list_updates_resolves_name():
    with (
        patch("linear_cli._resolve.execute", return_value=_projects_response()),
        patch(
            "linear_cli.project_updates.execute",
            return_value=_project_updates_response([_update_node()]),
        ),
    ):
        result = CliRunner().invoke(cli, ["project-updates", "list", "Alpha"])

    assert result.exit_code == 0
    assert "onTrack" in result.output


def test_list_updates_truncates_long_body():
    long_body = "x" * 300
    with patch(
        "linear_cli.project_updates.execute",
        return_value=_project_updates_response([_update_node(body=long_body)]),
    ):
        result = CliRunner().invoke(cli, ["project-updates", "list", _PROJ_UUID])

    assert result.exit_code == 0
    assert "..." in result.output
    # Preview should not exceed 200 chars + ellipsis
    assert "x" * 201 not in result.output


def test_list_updates_workspace_wide():
    nodes = [
        _update_node(body="All good.", health="onTrack", user_name="Alice", project_name="Alpha"),
        _update_node(
            update_id="upd-uuid-2",
            body="Delayed.",
            health="atRisk",
            user_name="Bob",
            project_name="Beta",
        ),
    ]
    with patch(
        "linear_cli.project_updates.execute",
        return_value={"projectUpdates": {"pageInfo": {"hasNextPage": False}, "nodes": nodes}},
    ):
        result = CliRunner().invoke(cli, ["project-updates", "list"])

    assert result.exit_code == 0
    assert "onTrack" in result.output
    assert "Alice" in result.output
    assert "(Alpha)" in result.output
    assert "atRisk" in result.output
    assert "(Beta)" in result.output


def test_add_update_success():
    mutation_response = {
        "projectUpdateCreate": {
            "success": True,
            "projectUpdate": {
                "id": "upd-uuid-new",
                "health": "atRisk",
                "createdAt": "2026-07-17T00:00:00Z",
                "url": "https://linear.app/update/upd-uuid-new",
            },
        }
    }
    with patch(
        "linear_cli.project_updates.execute",
        return_value=mutation_response,
    ):
        result = CliRunner().invoke(
            cli,
            ["project-updates", "add", _PROJ_UUID, "--body", "Status update", "--health", "atRisk"],
        )

    assert result.exit_code == 0
    assert "upd-uuid-new" in result.output
    assert "atRisk" in result.output
