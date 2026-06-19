"""Tests for comments commands including the edit subcommand."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def test_comments_list_shows_comments():
    nodes = [
        {
            "id": "c-uuid-1",
            "body": "Great work!",
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-01-01T00:00:00Z",
            "user": {"name": "Alice"},
        }
    ]
    with patch(
        "linear_cli.comments.paginate",
        return_value=nodes,
    ):
        result = CliRunner().invoke(cli, ["comments", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "Great work!" in result.output


def test_comments_list_empty():
    with patch("linear_cli.comments.paginate", return_value=[]):
        result = CliRunner().invoke(cli, ["comments", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "no comments" in result.output


def test_comments_edit_updates_comment():
    with patch(
        "linear_cli.comments.execute",
        return_value={
            "commentUpdate": {
                "success": True,
                "comment": {
                    "id": "c-uuid-1",
                    "body": "Updated body",
                    "updatedAt": "2026-06-18T00:00:00Z",
                },
            }
        },
    ):
        result = CliRunner().invoke(cli, ["comments", "edit", "c-uuid-1", "--body", "Updated body"])

    assert result.exit_code == 0
    assert "comment updated" in result.output
    assert "c-uuid-1" in result.output


def test_comments_edit_failure():
    with patch(
        "linear_cli.comments.execute",
        return_value={"commentUpdate": {"success": False}},
    ):
        result = CliRunner().invoke(cli, ["comments", "edit", "c-uuid-1", "--body", "New text"])

    assert result.exit_code != 0
