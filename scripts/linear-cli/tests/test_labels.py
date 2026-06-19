"""Tests for the labels groups and list commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _label_node(
    name: str = "Bug",
    is_group: bool = False,
    parent_name: str | None = None,
    color: str = "#ff0000",
) -> dict:
    return {
        "id": f"label-{name.lower().replace(' ', '-')}",
        "name": name,
        "color": color,
        "isGroup": is_group,
        "parent": {"id": "parent-id", "name": parent_name} if parent_name else None,
    }


def _group_node(name: str = "Ticket Type", color: str = "#0000ff") -> dict:
    return {"id": f"group-{name.lower().replace(' ', '-')}", "name": name, "color": color}


def _child_node(name: str = "Bug") -> dict:
    return {"id": f"child-{name.lower().replace(' ', '-')}", "name": name, "color": "#ff0000"}


# --- labels groups ---


def test_labels_groups_lists_group_names():
    data = {"issueLabels": {"nodes": [_group_node("Ticket Type"), _group_node("Priority")]}}
    with patch("linear_cli.labels.execute", return_value=data):
        result = CliRunner().invoke(cli, ["labels", "groups"])

    assert result.exit_code == 0
    assert "Ticket Type\n" in result.output
    assert "Priority\n" in result.output
    assert "(group)" not in result.output


def test_labels_groups_with_team_resolves_team_id():
    teams_data = {"teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}}
    labels_data = {"issueLabels": {"nodes": [_group_node("Ticket Type")]}}
    with (
        patch("linear_cli._resolve.execute", return_value=teams_data),
        patch("linear_cli.labels.execute", return_value=labels_data),
    ):
        result = CliRunner().invoke(cli, ["labels", "groups", "--team", "ENG"])

    assert result.exit_code == 0
    assert "Ticket Type" in result.output


def test_labels_groups_no_groups_found():
    data = {"issueLabels": {"nodes": []}}
    with patch("linear_cli.labels.execute", return_value=data):
        result = CliRunner().invoke(cli, ["labels", "groups"])

    assert result.exit_code == 0
    assert "no groups found" in result.output


# --- labels list (default: no --group) ---


def test_labels_list_default_shows_groups_with_suffix_and_ungrouped_plain():
    nodes = [
        _label_node("Ticket Type", is_group=True),
        _label_node("Bug", is_group=False, parent_name="Ticket Type"),
        _label_node("Feature", is_group=False, parent_name=None),
    ]
    with patch("linear_cli.labels.paginate", return_value=nodes):
        result = CliRunner().invoke(cli, ["labels", "list"])

    assert result.exit_code == 0
    assert "Ticket Type (group)" in result.output
    assert "Feature" in result.output
    # Child label has a parent so it is excluded from ungrouped
    assert "Bug" not in result.output
    # Children are not expanded
    lines = result.output.strip().splitlines()
    assert not any(line.startswith("  ") for line in lines)


def test_labels_list_default_no_labels():
    with patch("linear_cli.labels.paginate", return_value=[]):
        result = CliRunner().invoke(cli, ["labels", "list"])

    assert result.exit_code == 0
    assert "no labels found" in result.output


def test_labels_list_default_with_team_resolves_team_id():
    teams_data = {"teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}}
    nodes = [_label_node("Bug", is_group=False, parent_name=None)]
    with (
        patch("linear_cli._resolve.execute", return_value=teams_data),
        patch("linear_cli.labels.paginate", return_value=nodes),
    ):
        result = CliRunner().invoke(cli, ["labels", "list", "--team", "ENG"])

    assert result.exit_code == 0
    assert "Bug" in result.output


# --- labels list --group ---


def test_labels_list_group_shows_group_header_and_indented_children():
    children_data = {"issueLabels": {"nodes": [_child_node("Bug"), _child_node("Improvement")]}}
    with patch("linear_cli.labels.execute", return_value=children_data):
        result = CliRunner().invoke(cli, ["labels", "list", "--group", "Ticket Type"])

    assert result.exit_code == 0
    assert "Ticket Type (group)" in result.output
    assert "  Bug" in result.output
    assert "  Improvement" in result.output


def test_labels_list_multiple_groups_listed_sequentially():
    def fake_execute(query, variables=None):
        parent = (variables or {}).get("filter", {}).get("parent", {}).get("name", {}).get("eq")
        if parent == "Ticket Type":
            return {"issueLabels": {"nodes": [_child_node("Bug")]}}
        if parent == "Priority":
            return {"issueLabels": {"nodes": [_child_node("High"), _child_node("Low")]}}
        return {"issueLabels": {"nodes": []}}

    with patch("linear_cli.labels.execute", side_effect=fake_execute):
        result = CliRunner().invoke(
            cli, ["labels", "list", "--group", "Ticket Type", "--group", "Priority"]
        )

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines[0] == "Ticket Type (group)"
    assert lines[1] == "  Bug"
    assert lines[2] == "Priority (group)"
    assert lines[3] == "  High"
    assert lines[4] == "  Low"


def test_labels_list_group_empty_group_shows_header_only():
    children_data = {"issueLabels": {"nodes": []}}
    with patch("linear_cli.labels.execute", return_value=children_data):
        result = CliRunner().invoke(cli, ["labels", "list", "--group", "Empty"])

    assert result.exit_code == 0
    assert "Empty (group)" in result.output
    # No indented children
    assert "  " not in result.output


def test_labels_list_group_with_team_resolves_team_id():
    teams_data = {"teams": {"nodes": [{"id": "team-uuid", "key": "ENG", "name": "Engineering"}]}}
    children_data = {"issueLabels": {"nodes": [_child_node("Bug")]}}
    with (
        patch("linear_cli._resolve.execute", return_value=teams_data),
        patch("linear_cli.labels.execute", return_value=children_data),
    ):
        result = CliRunner().invoke(
            cli, ["labels", "list", "--team", "ENG", "--group", "Ticket Type"]
        )

    assert result.exit_code == 0
    assert "Ticket Type (group)" in result.output
    assert "  Bug" in result.output
