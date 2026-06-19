"""Tests for the issues list and view commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _issue_node(
    identifier: str = "ENG-1",
    title: str = "Fix the thing",
    state_name: str = "In Progress",
    state_type: str = "started",
    priority: int = 2,
    assignee_name: str | None = "Bob",
    labels: list[str] | None = None,
) -> dict:
    return {
        "id": "issue-uuid-1",
        "identifier": identifier,
        "title": title,
        "description": "Some description",
        "priority": priority,
        "url": "https://linear.app/team/issue/ENG-1",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "state": {"name": state_name, "type": state_type},
        "assignee": {"name": assignee_name} if assignee_name else None,
        "labels": {"nodes": [{"name": ln} for ln in (labels or [])]},
    }


def _paginate_return(nodes: list) -> list:
    return nodes


def test_issues_list_shows_identifiers():
    with patch("linear_cli.issues.paginate", return_value=[_issue_node()]):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert result.exit_code == 0
    assert "ENG-1" in result.output
    assert "Fix the thing" in result.output


def test_issues_list_with_team_resolves_team():
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={
                "teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}
            },
        ),
        patch("linear_cli.issues.paginate", return_value=[_issue_node()]),
    ):
        result = CliRunner().invoke(cli, ["issues", "list", "--team", "ENG"])

    assert result.exit_code == 0
    assert "ENG-1" in result.output


def test_issues_list_empty():
    with patch("linear_cli.issues.paginate", return_value=[]):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert result.exit_code == 0
    assert "no issues found" in result.output


def test_issues_view_shows_detail():
    issue_data = {"issue": _issue_node()}
    with patch("linear_cli.issues.execute", return_value=issue_data):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "Fix the thing" in result.output
    assert "In Progress" in result.output
    assert "High" in result.output  # priority 2 = High


def test_issues_view_not_found():
    with patch("linear_cli.issues.execute", return_value={"issue": None}):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-999"])

    assert result.exit_code != 0


def test_issues_list_priority_labels():
    nodes = [_issue_node(priority=0), _issue_node(identifier="ENG-2", priority=1)]
    with patch("linear_cli.issues.paginate", return_value=nodes):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert "None" in result.output
    assert "Urgent" in result.output
