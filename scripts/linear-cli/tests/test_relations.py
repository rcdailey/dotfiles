"""Tests for the relations commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _relation_node(
    rel_id: str = "rel-uuid-1",
    rel_type: str = "blocks",
    identifier: str = "ENG-42",
    title: str = "Blocked issue",
) -> dict:
    return {
        "id": rel_id,
        "type": rel_type,
        "relatedIssue": {"identifier": identifier, "title": title},
    }


def _issue_with_relations(nodes: list) -> dict:
    return {"issue": {"relations": {"nodes": nodes}}}


def test_relations_list_shows_relations():
    with patch(
        "linear_cli.relations.execute",
        return_value=_issue_with_relations([_relation_node()]),
    ):
        result = CliRunner().invoke(cli, ["relations", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "blocks" in result.output
    assert "ENG-42" in result.output
    assert "Blocked issue" in result.output


def test_relations_list_empty():
    with patch(
        "linear_cli.relations.execute",
        return_value=_issue_with_relations([]),
    ):
        result = CliRunner().invoke(cli, ["relations", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "no relations" in result.output


def test_relations_list_blocked_by_display():
    node = _relation_node(rel_type="blockedBy", identifier="ENG-10", title="Blocking issue")
    with patch(
        "linear_cli.relations.execute",
        return_value=_issue_with_relations([node]),
    ):
        result = CliRunner().invoke(cli, ["relations", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "blocked-by" in result.output
    assert "ENG-10" in result.output


def test_relations_add():
    with patch(
        "linear_cli.relations.execute",
        return_value={
            "issueRelationCreate": {
                "success": True,
                "issueRelation": {"id": "rel-uuid-2", "type": "blocks"},
            }
        },
    ):
        result = CliRunner().invoke(cli, ["relations", "add", "ENG-1", "blocks", "ENG-42"])

    assert result.exit_code == 0
    assert "relation created" in result.output


def test_relations_remove():
    list_response = _issue_with_relations([_relation_node(rel_id="rel-uuid-1")])
    delete_response = {"issueRelationDelete": {"success": True}}

    with patch(
        "linear_cli.relations.execute",
        side_effect=[list_response, delete_response],
    ):
        result = CliRunner().invoke(cli, ["relations", "remove", "ENG-1", "blocks", "ENG-42"])

    assert result.exit_code == 0
    assert "relation removed" in result.output


def test_relations_remove_not_found():
    with patch(
        "linear_cli.relations.execute",
        return_value=_issue_with_relations([]),
    ):
        result = CliRunner().invoke(cli, ["relations", "remove", "ENG-1", "blocks", "ENG-99"])

    assert result.exit_code != 0
