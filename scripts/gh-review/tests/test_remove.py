"""Tests for the remove subcommand."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli


def test_remove_success():
    with patch("gh_review.remove.gh_rest", return_value="") as mock_rest:
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "123"])

    assert result.exit_code == 0
    assert "removed: 123" in result.output
    mock_rest.assert_called_once_with("DELETE", "repos/owner/repo/pulls/comments/123")


def test_remove_api_error():
    with patch("gh_review.remove.gh_rest", side_effect=GhError("API error occurred")):
        result = CliRunner().invoke(cli, ["remove", "owner/repo", "999"])

    assert result.exit_code == 1
    assert "API error occurred" in result.output


def test_remove_missing_args():
    result = CliRunner().invoke(cli, ["remove", "owner/repo"])
    assert result.exit_code != 0
