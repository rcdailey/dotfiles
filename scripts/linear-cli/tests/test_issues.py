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
    estimate: float | None = None,
    parent: dict | None = None,
    children: list[dict] | None = None,
    comment_count: int = 0,
) -> dict:
    return {
        "id": "issue-uuid-1",
        "identifier": identifier,
        "title": title,
        "description": "Some description",
        "priority": priority,
        "estimate": estimate,
        "url": "https://linear.app/team/issue/ENG-1",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
        "state": {"name": state_name, "type": state_type},
        "assignee": {"name": assignee_name} if assignee_name else None,
        "labels": {"nodes": [{"name": ln} for ln in (labels or [])]},
        "parent": parent,
        "children": {"nodes": children or []},
        "comments": {"nodes": [{"id": str(i)} for i in range(comment_count)]},
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


def test_issues_view_shows_comment_count():
    issue_data = {"issue": _issue_node(comment_count=5)}
    with patch("linear_cli.issues.execute", return_value=issue_data):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "comments:    5" in result.output


def test_issues_view_not_found():
    with patch("linear_cli.issues.execute", return_value={"issue": None}):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-999"])

    assert result.exit_code != 0


def test_issues_search_returns_results():
    with patch("linear_cli.issues.paginate", return_value=[_issue_node()]):
        result = CliRunner().invoke(cli, ["issues", "search", "fix the thing"])

    assert result.exit_code == 0
    assert "ENG-1" in result.output
    assert "Fix the thing" in result.output


def test_issues_search_with_team_filter():
    with (
        patch(
            "linear_cli._resolve.execute",
            return_value={
                "teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}
            },
        ),
        patch("linear_cli.issues.paginate", return_value=[_issue_node()]) as mock_pag,
    ):
        result = CliRunner().invoke(cli, ["issues", "search", "fix the thing", "--team", "ENG"])

    assert result.exit_code == 0
    assert "ENG-1" in result.output
    call_vars = mock_pag.call_args[0][1]
    assert call_vars["term"] == "fix the thing"
    assert call_vars["filter"]["team"]["id"]["eq"] == "team-uuid"


def test_issues_search_empty():
    with patch("linear_cli.issues.paginate", return_value=[]):
        result = CliRunner().invoke(cli, ["issues", "search", "nonexistent"])

    assert result.exit_code == 0
    assert "no issues found" in result.output


def test_issues_list_priority_labels():
    nodes = [_issue_node(priority=0), _issue_node(identifier="ENG-2", priority=1)]
    with patch("linear_cli.issues.paginate", return_value=nodes):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert "None" in result.output
    assert "Urgent" in result.output


def test_issues_list_shows_estimate():
    with patch("linear_cli.issues.paginate", return_value=[_issue_node(estimate=3.0)]):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert result.exit_code == 0
    assert "estimate: 3" in result.output


def test_issues_list_estimate_none_shown_as_dash():
    with patch("linear_cli.issues.paginate", return_value=[_issue_node(estimate=None)]):
        result = CliRunner().invoke(cli, ["issues", "list"])

    assert result.exit_code == 0
    assert "estimate: -" in result.output


def test_issues_list_with_cycle_filter():
    with (
        patch(
            "linear_cli.issues.resolve_team_id",
            return_value="team-uuid",
        ),
        patch(
            "linear_cli.issues.resolve_cycle_number",
            return_value=5,
        ),
        patch("linear_cli.issues.paginate", return_value=[_issue_node()]) as mock_pag,
    ):
        result = CliRunner().invoke(cli, ["issues", "list", "--team", "ENG", "--cycle", "active"])

    assert result.exit_code == 0
    call_vars = mock_pag.call_args[0][1]
    assert call_vars["filter"]["cycle"] == {"number": {"eq": 5}}


def test_issues_list_cycle_requires_team():
    result = CliRunner().invoke(cli, ["issues", "list", "--cycle", "active"])

    assert result.exit_code != 0
    assert "error: --cycle requires --team" in result.output


def test_issues_list_with_estimate_none_filter():
    with patch("linear_cli.issues.paginate", return_value=[]) as mock_pag:
        CliRunner().invoke(cli, ["issues", "list", "--estimate", "none"])

    call_vars = mock_pag.call_args[0][1]
    assert call_vars["filter"]["estimate"] == {"null": True}


def test_issues_list_with_estimate_value_filter():
    with patch("linear_cli.issues.paginate", return_value=[]) as mock_pag:
        CliRunner().invoke(cli, ["issues", "list", "--estimate", "5"])

    call_vars = mock_pag.call_args[0][1]
    assert call_vars["filter"]["estimate"] == {"eq": 5.0}


def test_issues_view_shows_estimate():
    issue_data = {"issue": _issue_node(estimate=5.0)}
    with patch("linear_cli.issues.execute", return_value=issue_data):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "estimate:    5" in result.output


def test_issues_view_shows_parent():
    node = _issue_node(parent={"identifier": "ENG-100", "title": "Epic task"})
    with patch("linear_cli.issues.execute", return_value={"issue": node}):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "parent:      ENG-100  Epic task" in result.output


def test_issues_view_shows_children():
    children = [
        {
            "identifier": "ENG-2",
            "title": "Sub-task A",
            "state": {"name": "Todo"},
            "priority": 3,
            "assignee": {"name": "Alice"},
            "labels": {"nodes": [{"name": "Backend"}]},
            "estimate": 2.0,
        },
        {
            "identifier": "ENG-3",
            "title": "Sub-task B",
            "state": {"name": "Done"},
            "priority": 4,
            "assignee": None,
            "labels": {"nodes": []},
            "estimate": None,
        },
    ]
    node = _issue_node(children=children)
    with patch("linear_cli.issues.execute", return_value={"issue": node}):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "sub-issues (2):" in result.output
    assert "ENG-2" in result.output
    assert "Sub-task A" in result.output
    assert "ENG-3" in result.output
    assert "Sub-task B" in result.output


def test_issues_view_no_children_omits_section():
    with patch("linear_cli.issues.execute", return_value={"issue": _issue_node()}):
        result = CliRunner().invoke(cli, ["issues", "view", "ENG-1"])

    assert result.exit_code == 0
    assert "sub-issues" not in result.output


def test_issues_create_with_milestone():
    with (
        patch(
            "linear_cli._resolve.execute",
            side_effect=[
                {"teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}},
                {"projects": {"nodes": [{"id": "proj-uuid", "name": "Sprint 42"}]}},
                {
                    "projectMilestones": {
                        "nodes": [{"id": "ms-uuid", "name": "Beta Launch", "project": {}}]
                    }
                },
            ],
        ),
        patch(
            "linear_cli.issues.execute",
            return_value={
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "issue-uuid",
                        "identifier": "ENG-99",
                        "title": "Test",
                        "url": "https://linear.app/ENG-99",
                    },
                }
            },
        ) as mock_exec,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "issues",
                "create",
                "--title",
                "Test",
                "--team",
                "ENG",
                "--project",
                "Sprint 42",
                "--milestone",
                "Beta Launch",
            ],
        )

    assert result.exit_code == 0
    assert "ENG-99" in result.output
    call_args = mock_exec.call_args[0]
    call_input = call_args[1]["input"]
    assert call_input["projectMilestoneId"] == "ms-uuid"


def test_issues_create_milestone_requires_project():
    with patch(
        "linear_cli._resolve.execute",
        return_value={
            "teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}
        },
    ):
        result = CliRunner().invoke(
            cli,
            ["issues", "create", "--title", "Test", "--team", "ENG", "--milestone", "Beta"],
        )

    assert result.exit_code != 0


def test_issues_update_with_milestone():
    issue_node = {
        **_issue_node(),
        "team": {"id": "team-uuid", "key": "ENG"},
        "project": {"id": "proj-uuid", "name": "Sprint 42"},
        "labels": {"nodes": []},
    }
    with (
        patch(
            "linear_cli.issues.execute",
            side_effect=[
                {"issue": issue_node},
                {
                    "issueUpdate": {
                        "success": True,
                        "issue": {"id": "issue-uuid", "identifier": "ENG-1", "title": "Fix"},
                    }
                },
            ],
        ),
        patch(
            "linear_cli._resolve.execute",
            return_value={
                "projectMilestones": {
                    "nodes": [{"id": "ms-uuid", "name": "Beta Launch", "project": {}}]
                }
            },
        ),
    ):
        result = CliRunner().invoke(
            cli, ["issues", "update", "ENG-1", "--milestone", "Beta Launch"]
        )

    assert result.exit_code == 0
    assert "updated" in result.output
