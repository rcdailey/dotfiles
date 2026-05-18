"""Tests for the remove subcommand."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli

_DELETE_RESPONSE = {
    "data": {"deletePullRequestReviewComment": {"pullRequestReviewComment": {"databaseId": 456}}}
}


def test_remove_success():
    with patch("gh_review.remove.gh_graphql_mutation", return_value=_DELETE_RESPONSE):
        result = CliRunner().invoke(cli, ["remove", "PRRC_abc123"])

    assert result.exit_code == 0
    assert "removed: 456" in result.output


def test_remove_error():
    with patch(
        "gh_review.remove.gh_graphql_mutation",
        side_effect=GhError("Could not resolve to a node"),
    ):
        result = CliRunner().invoke(cli, ["remove", "PRRC_bad"])

    assert result.exit_code == 1
    assert "Could not resolve to a node" in result.output


def test_remove_missing_arg():
    result = CliRunner().invoke(cli, ["remove"])
    assert result.exit_code != 0
