"""Tests for the edit subcommand."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli

_CURRENT_COMMENT: dict[str, Any] = {
    "body": "original body",
    "path": "src/main.ts",
    "line": 10,
    "start_line": None,
    "side": "RIGHT",
    "start_side": None,
}

_THREAD_RESPONSE: dict[str, Any] = {
    "data": {
        "addPullRequestReviewThread": {
            "thread": {
                "id": "PRRT_new123",
                "path": "src/main.ts",
                "isOutdated": False,
                "line": 10,
                "startLine": None,
                "diffSide": "RIGHT",
            }
        }
    }
}


def test_body_only_edit():
    with patch("gh_review.edit.gh_rest", return_value="{}") as mock_rest:
        result = CliRunner().invoke(cli, ["edit", "owner/repo", "456", "--body", "new body"])

    assert result.exit_code == 0
    assert "edited: 456 (body updated)" in result.output
    mock_rest.assert_called_once_with(
        "PATCH",
        "repos/owner/repo/pulls/comments/456",
        body={"body": "new body"},
    )


def test_body_only_edit_comment_not_found():
    with patch("gh_review.edit.gh_rest", side_effect=GhError("HTTP 404: Not Found")):
        result = CliRunner().invoke(cli, ["edit", "owner/repo", "456", "--body", "x"])

    assert result.exit_code == 1
    assert "comment 456 not found" in result.output


def test_no_options_error():
    result = CliRunner().invoke(cli, ["edit", "owner/repo", "123"])

    assert result.exit_code == 1
    assert "at least one option required" in result.output


def test_positioning_without_review_id():
    result = CliRunner().invoke(cli, ["edit", "owner/repo", "123", "--line", "20"])

    assert result.exit_code == 1
    assert "--review-id required when changing position" in result.output


def test_invalid_review_id_format():
    result = CliRunner().invoke(
        cli,
        ["edit", "owner/repo", "123", "--line", "20", "--review-id", "BAD_ID"],
    )

    assert result.exit_code == 1
    assert "invalid review id: BAD_ID (expected PRR_... node id)" in result.output


def test_reposition_edit():
    def rest_side_effect(method: str, endpoint: str, **kwargs: Any) -> str:
        if method == "GET":
            return json.dumps(_CURRENT_COMMENT)
        return ""  # DELETE returns empty 204

    with (
        patch("gh_review.edit.gh_rest", side_effect=rest_side_effect),
        patch("gh_review.edit.gh_graphql_mutation", return_value=_THREAD_RESPONSE) as mock_gql,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "edit",
                "owner/repo",
                "789",
                "--review-id",
                "PRR_abc",
                "--line",
                "20",
            ],
        )

    assert result.exit_code == 0
    assert "edited: 789 -> PRRT_new123 (repositioned)" in result.output
    # Verify mutation received merged fields (line overridden, rest from current).
    mutation_input = mock_gql.call_args[0][1]["input"]
    assert mutation_input["line"] == 20
    assert mutation_input["path"] == "src/main.ts"
    assert mutation_input["body"] == "original body"
    assert mutation_input["pullRequestReviewId"] == "PRR_abc"


def test_reposition_merges_body_override():
    """When --body and positioning args are both supplied, body is overridden too."""

    def rest_side_effect(method: str, endpoint: str, **kwargs: Any) -> str:
        if method == "GET":
            return json.dumps(_CURRENT_COMMENT)
        return ""

    with (
        patch("gh_review.edit.gh_rest", side_effect=rest_side_effect),
        patch("gh_review.edit.gh_graphql_mutation", return_value=_THREAD_RESPONSE) as mock_gql,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "edit",
                "owner/repo",
                "789",
                "--review-id",
                "PRR_abc",
                "--line",
                "20",
                "--body",
                "updated body",
            ],
        )

    assert result.exit_code == 0
    mutation_input = mock_gql.call_args[0][1]["input"]
    assert mutation_input["body"] == "updated body"


def test_reposition_get_not_found():
    with patch("gh_review.edit.gh_rest", side_effect=GhError("HTTP 404: Not Found")):
        result = CliRunner().invoke(
            cli,
            ["edit", "owner/repo", "789", "--review-id", "PRR_abc", "--line", "5"],
        )

    assert result.exit_code == 1
    assert "comment 789 not found" in result.output


def test_delete_succeeds_create_fails():
    """When DELETE succeeds but the GraphQL mutation fails, warn about lost comment."""

    def rest_side_effect(method: str, endpoint: str, **kwargs: Any) -> str:
        if method == "GET":
            return json.dumps(_CURRENT_COMMENT)
        return ""  # DELETE succeeds

    with (
        patch("gh_review.edit.gh_rest", side_effect=rest_side_effect),
        patch("gh_review.edit.gh_graphql_mutation", side_effect=GhError("mutation failed")),
    ):
        result = CliRunner().invoke(
            cli,
            ["edit", "owner/repo", "789", "--review-id", "PRR_abc", "--line", "5"],
        )

    assert result.exit_code == 1
    assert "mutation failed" in result.output
    assert "was deleted but could not be recreated" in result.output
