"""Tests for the states commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _state_node(
    name: str = "In Progress",
    state_type: str = "started",
    position: float = 1.0,
) -> dict:
    return {
        "id": "state-uuid-1",
        "name": name,
        "type": state_type,
        "color": "#f2c94c",
        "position": position,
    }


def test_states_list():
    data = {
        "workflowStates": {
            "nodes": [
                _state_node("Triage", "triage", 0.0),
                _state_node("In Progress", "started", 1.0),
            ]
        }
    }
    with patch("linear_cli.states.execute", return_value=data):
        result = CliRunner().invoke(cli, ["states", "list"])

    assert result.exit_code == 0
    assert "Triage" in result.output
    assert "In Progress" in result.output


def test_states_list_with_team():
    data = {"workflowStates": {"nodes": [_state_node()]}}
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={
                "teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}
            },
        ),
        patch("linear_cli.states.execute", return_value=data),
    ):
        result = CliRunner().invoke(cli, ["states", "list", "--team", "ENG"])

    assert result.exit_code == 0
    assert "In Progress" in result.output


def test_states_list_empty():
    data = {"workflowStates": {"nodes": []}}
    with patch("linear_cli.states.execute", return_value=data):
        result = CliRunner().invoke(cli, ["states", "list"])

    assert result.exit_code == 0
    assert "no states found" in result.output
