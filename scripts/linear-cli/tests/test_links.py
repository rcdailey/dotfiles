"""Tests for the links commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _issue_with_attachments(nodes: list) -> dict:
    return {"issue": {"attachments": {"nodes": nodes}}}


def test_links_list_shows_links():
    att = {"id": "att-uuid-1", "title": "Docs", "url": "https://example.com/docs"}
    with patch("linear_cli.links.execute", return_value=_issue_with_attachments([att])):
        result = CliRunner().invoke(cli, ["links", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "Docs" in result.output
    assert "https://example.com/docs" in result.output


def test_links_list_no_title():
    att = {"id": "att-uuid-2", "title": None, "url": "https://example.com"}
    with patch("linear_cli.links.execute", return_value=_issue_with_attachments([att])):
        result = CliRunner().invoke(cli, ["links", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "https://example.com" in result.output


def test_links_list_empty():
    with patch("linear_cli.links.execute", return_value=_issue_with_attachments([])):
        result = CliRunner().invoke(cli, ["links", "list", "ENG-1"])

    assert result.exit_code == 0
    assert "no links" in result.output


def test_links_add():
    with patch(
        "linear_cli.links.execute",
        return_value={
            "attachmentLinkURL": {
                "success": True,
                "attachment": {"id": "att-uuid-3", "title": "PR", "url": "https://github.com/pr/1"},
            }
        },
    ):
        result = CliRunner().invoke(
            cli, ["links", "add", "ENG-1", "https://github.com/pr/1", "--title", "PR"]
        )

    assert result.exit_code == 0
    assert "link added" in result.output


def test_links_remove():
    with patch(
        "linear_cli.links.execute",
        return_value={"attachmentDelete": {"success": True}},
    ):
        result = CliRunner().invoke(cli, ["links", "remove", "att-uuid-1"])

    assert result.exit_code == 0
    assert "link removed" in result.output
