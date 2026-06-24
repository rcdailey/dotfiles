"""Tests for the teams commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _team_node(key: str = "ENG", name: str = "Engineering") -> dict:
    return {"id": "team-uuid-1", "key": key, "name": name}


def _member_node(
    name: str = "Alice",
    email: str = "alice@example.com",
    active: bool = True,
) -> dict:
    return {
        "id": "user-uuid-1",
        "name": name,
        "displayName": name,
        "email": email,
        "active": active,
    }


def test_teams_list():
    data = {"teams": {"nodes": [_team_node(), _team_node("OPS", "Operations")]}}
    with patch("linear_cli.teams.execute", return_value=data):
        result = CliRunner().invoke(cli, ["teams", "list"])

    assert result.exit_code == 0
    assert "ENG" in result.output
    assert "OPS" in result.output


def test_teams_list_empty():
    data = {"teams": {"nodes": []}}
    with patch("linear_cli.teams.execute", return_value=data):
        result = CliRunner().invoke(cli, ["teams", "list"])

    assert result.exit_code == 0
    assert "no teams found" in result.output


def test_teams_members():
    data = {
        "team": {
            "members": {
                "nodes": [
                    _member_node("Alice", "alice@example.com", True),
                    _member_node("Bob", "bob@example.com", False),
                ]
            }
        }
    }
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={"teams": {"nodes": [_team_node()]}},
        ),
        patch("linear_cli.teams.execute", return_value=data),
    ):
        result = CliRunner().invoke(cli, ["teams", "members", "ENG"])

    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "[active]" in result.output
    assert "Bob" in result.output
    assert "[inactive]" in result.output


def test_teams_members_empty():
    data = {"team": {"members": {"nodes": []}}}
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={"teams": {"nodes": [_team_node()]}},
        ),
        patch("linear_cli.teams.execute", return_value=data),
    ):
        result = CliRunner().invoke(cli, ["teams", "members", "ENG"])

    assert result.exit_code == 0
    assert "no members found" in result.output
