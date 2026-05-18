"""Tests for the remove subcommand."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli


# -- REST (database ID) --------------------------------------------------------


def test_remove_success():
    with patch("gh_review.remove.gh_rest", return_value="") as mock_rest:
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "123"])

    assert result.exit_code == 0
    assert "removed: 123" in result.output
    mock_rest.assert_called_once_with("DELETE", "repos/owner/repo/pulls/comments/123")


def test_remove_404():
    with patch("gh_review.remove.gh_rest", side_effect=GhError("HTTP 404: Not Found")):
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "999"])

    assert result.exit_code == 1
    assert "comment 999 not found" in result.output


def test_remove_api_error():
    with patch("gh_review.remove.gh_rest", side_effect=GhError("server error")):
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "999"])

    assert result.exit_code == 1
    assert "server error" in result.output


def test_remove_missing_args():
    result = CliRunner().invoke(cli, ["remove", "owner/repo"])
    assert result.exit_code != 0


# -- GraphQL (node ID) ---------------------------------------------------------


def test_remove_graphql_success():
    response = {
        "data": {
            "deletePullRequestReviewComment": {"pullRequestReviewComment": {"databaseId": 456}}
        }
    }
    with patch("gh_review.remove.gh_graphql_mutation", return_value=response):
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "PRRC_abc123"])

    assert result.exit_code == 0
    assert "removed: 456" in result.output


def test_remove_graphql_error():
    with patch(
        "gh_review.remove.gh_graphql_mutation",
        side_effect=GhError("Could not resolve to a node"),
    ):
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "PRRC_bad"])

    assert result.exit_code == 1
    assert "Could not resolve to a node" in result.output
