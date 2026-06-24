"""Tests for the raw GraphQL API command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def test_api_executes_query():
    data = {"viewer": {"id": "user-1", "name": "Alice"}}
    with patch("linear_cli.api.execute", return_value=data):
        result = CliRunner().invoke(cli, ["api", "query { viewer { id name } }"])

    assert result.exit_code == 0
    assert '"viewer"' in result.output
    assert '"Alice"' in result.output


def test_api_with_variables():
    data = {"issue": {"title": "Fix it"}}
    with patch("linear_cli.api.execute", return_value=data) as mock_exec:
        result = CliRunner().invoke(
            cli,
            ["api", "query($id: String!) { issue(id: $id) { title } }", "--var", "id=ENG-1"],
        )

    assert result.exit_code == 0
    call_vars = mock_exec.call_args[0][1]
    assert call_vars["id"] == "ENG-1"


def test_api_json_variable_parsing():
    data = {}
    with patch("linear_cli.api.execute", return_value=data) as mock_exec:
        result = CliRunner().invoke(
            cli,
            ["api", "mutation {}", "--var", "count=42", "--var", "flag=true"],
        )

    assert result.exit_code == 0
    call_vars = mock_exec.call_args[0][1]
    assert call_vars["count"] == 42
    assert call_vars["flag"] is True


def test_api_stdin_query():
    data = {"viewer": {"id": "user-1"}}
    with patch("linear_cli.api.execute", return_value=data):
        result = CliRunner().invoke(cli, ["api", "-"], input="query { viewer { id } }")

    assert result.exit_code == 0
    assert '"user-1"' in result.output


def test_api_invalid_variable_format():
    result = CliRunner().invoke(cli, ["api", "query {}", "--var", "badformat"])
    assert result.exit_code != 0
