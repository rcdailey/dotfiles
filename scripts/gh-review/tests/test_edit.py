"""Tests for the edit subcommand."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli

_UPDATE_RESPONSE: dict[str, Any] = {
    "data": {
        "updatePullRequestReviewComment": {
            "pullRequestReviewComment": {"databaseId": 456, "body": "new body"}
        }
    }
}

_DELETE_RESPONSE: dict[str, Any] = {
    "data": {"deletePullRequestReviewComment": {"pullRequestReviewComment": {"databaseId": 789}}}
}

_THREAD_RESPONSE: dict[str, Any] = {
    "data": {
        "addPullRequestReviewThread": {
            "thread": {
                "id": "PRRT_new123",
                "path": "src/main.ts",
                "isOutdated": False,
                "line": 20,
                "startLine": None,
                "diffSide": "RIGHT",
                "comments": {"nodes": [{"databaseId": 555, "id": "PRRC_new555"}]},
            }
        }
    }
}

_QUERY_COMMENT_RESPONSE: dict[str, Any] = {
    "data": {
        "node": {
            "body": "original body",
            "path": "src/main.ts",
        }
    }
}


# -- body-only -----------------------------------------------------------------


def test_body_only_edit():
    with patch("gh_review.edit.gh_graphql_mutation", return_value=_UPDATE_RESPONSE) as mock_gql:
        result = CliRunner().invoke(cli, ["edit", "PRRC_abc", "--body", "new body"])

    assert result.exit_code == 0
    assert "edited: 456 (body updated)" in result.output
    mutation_input = mock_gql.call_args[0][1]["input"]
    assert mutation_input["pullRequestReviewCommentId"] == "PRRC_abc"
    assert mutation_input["body"] == "new body"


def test_body_only_edit_error():
    with patch(
        "gh_review.edit.gh_graphql_mutation",
        side_effect=GhError("Could not resolve to a node"),
    ):
        result = CliRunner().invoke(cli, ["edit", "PRRC_bad", "--body", "x"])

    assert result.exit_code == 1
    assert "Could not resolve to a node" in result.output


# -- validation ----------------------------------------------------------------


def test_no_options_error():
    result = CliRunner().invoke(cli, ["edit", "PRRC_abc"])

    assert result.exit_code == 1
    assert "at least one option required" in result.output


def test_positioning_without_review_id():
    result = CliRunner().invoke(cli, ["edit", "PRRC_abc", "--line", "20"])

    assert result.exit_code == 1
    assert "--review-id required when changing position" in result.output


def test_invalid_review_id_format():
    result = CliRunner().invoke(
        cli,
        ["edit", "PRRC_abc", "--line", "20", "--review-id", "BAD_ID"],
    )

    assert result.exit_code == 1
    assert "invalid review id: BAD_ID (expected PRR_... node id)" in result.output


def test_reposition_requires_line():
    with patch("gh_review.edit.gh_graphql", return_value=_QUERY_COMMENT_RESPONSE):
        result = CliRunner().invoke(
            cli,
            ["edit", "PRRC_abc", "--review-id", "PRR_xyz", "--path", "other.ts"],
        )

    assert result.exit_code == 1
    assert "--line required when repositioning" in result.output


# -- reposition ----------------------------------------------------------------


def test_reposition():
    call_count = {"n": 0}

    def gql_side_effect(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _DELETE_RESPONSE
        return _THREAD_RESPONSE

    with (
        patch("gh_review.edit.gh_graphql", return_value=_QUERY_COMMENT_RESPONSE),
        patch("gh_review.edit.gh_graphql_mutation", side_effect=gql_side_effect) as mock_gql,
    ):
        result = CliRunner().invoke(
            cli,
            ["edit", "PRRC_abc", "--review-id", "PRR_xyz", "--line", "20"],
        )

    assert result.exit_code == 0
    assert "comment-id: 555" in result.output
    assert "comment-node-id: PRRC_new555" in result.output
    assert "path: src/main.ts" in result.output
    assert "line: L20" in result.output
    # Verify create mutation received merged fields.
    create_input = mock_gql.call_args_list[1][0][1]["input"]
    assert create_input["line"] == 20
    assert create_input["path"] == "src/main.ts"
    assert create_input["body"] == "original body"
    assert create_input["side"] == "RIGHT"


def test_reposition_with_body_override():
    call_count = {"n": 0}

    def gql_side_effect(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _DELETE_RESPONSE
        return _THREAD_RESPONSE

    with (
        patch("gh_review.edit.gh_graphql", return_value=_QUERY_COMMENT_RESPONSE),
        patch("gh_review.edit.gh_graphql_mutation", side_effect=gql_side_effect) as mock_gql,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "edit",
                "PRRC_abc",
                "--review-id",
                "PRR_xyz",
                "--line",
                "20",
                "--body",
                "updated body",
            ],
        )

    assert result.exit_code == 0
    create_input = mock_gql.call_args_list[1][0][1]["input"]
    assert create_input["body"] == "updated body"


def test_reposition_not_found():
    response: dict[str, Any] = {"data": {"node": None}}
    with patch("gh_review.edit.gh_graphql", return_value=response):
        result = CliRunner().invoke(
            cli,
            ["edit", "PRRC_bad", "--review-id", "PRR_xyz", "--line", "5"],
        )

    assert result.exit_code == 1
    assert "comment PRRC_bad not found" in result.output


def test_delete_ok_create_fails():
    """Delete succeeds but create fails; warn about lost comment."""

    def gql_side_effect(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if "deletePullRequestReviewComment" in query:
            return _DELETE_RESPONSE
        raise GhError("create failed")

    with (
        patch("gh_review.edit.gh_graphql", return_value=_QUERY_COMMENT_RESPONSE),
        patch("gh_review.edit.gh_graphql_mutation", side_effect=gql_side_effect),
    ):
        result = CliRunner().invoke(
            cli,
            ["edit", "PRRC_abc", "--review-id", "PRR_xyz", "--line", "20"],
        )

    assert result.exit_code == 1
    assert "create failed" in result.output
    assert "was deleted but could not be recreated" in result.output
