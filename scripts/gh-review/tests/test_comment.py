"""Tests for the comment subcommand."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gh_review._errors import GhError
from gh_review.cli import cli


def _thread_response(
    thread_id: str = "PRRT_abc",
    path: str = "src/foo.ts",
    line: int | None = 42,
    start_line: int | None = None,
    subject_type: str = "LINE",
    comment_db_id: int = 100,
    comment_node_id: str = "PRRC_100",
    is_outdated: bool = False,
) -> dict[str, Any]:
    return {
        "data": {
            "addPullRequestReviewThread": {
                "thread": {
                    "id": thread_id,
                    "path": path,
                    "isOutdated": is_outdated,
                    "line": line,
                    "startLine": start_line,
                    "diffSide": "RIGHT",
                    "subjectType": subject_type,
                    "comments": {"nodes": [{"databaseId": comment_db_id, "id": comment_node_id}]},
                }
            }
        }
    }


_NULL_THREAD: dict[str, Any] = {"data": {"addPullRequestReviewThread": {"thread": None}}}


# -- line-level ----------------------------------------------------------------


def test_single_line_comment():
    resp = _thread_response()
    with patch("gh_review.comment.gh_graphql_mutation", return_value=resp):
        result = CliRunner().invoke(
            cli,
            [
                "comment",
                "--review-id",
                "PRR_x",
                "--path",
                "src/foo.ts",
                "--line",
                "42",
                "--body",
                "looks wrong",
            ],
        )

    assert result.exit_code == 0
    assert "id: PRRT_abc" in result.output
    assert "comment-id: 100" in result.output
    assert "comment-node-id: PRRC_100" in result.output
    assert "path: src/foo.ts" in result.output
    assert "line: L42" in result.output


def test_multi_line_comment():
    resp = _thread_response(start_line=10, line=20)
    with patch("gh_review.comment.gh_graphql_mutation", return_value=resp):
        result = CliRunner().invoke(
            cli,
            [
                "comment",
                "--review-id",
                "PRR_x",
                "--path",
                "src/foo.ts",
                "--start-line",
                "10",
                "--line",
                "20",
                "--body",
                "range comment",
            ],
        )

    assert result.exit_code == 0
    assert "line: L10-20" in result.output


def test_outdated_warning():
    resp = _thread_response(is_outdated=True)
    with patch("gh_review.comment.gh_graphql_mutation", return_value=resp):
        result = CliRunner().invoke(
            cli,
            ["comment", "--review-id", "PRR_x", "--path", "f.ts", "--line", "1", "--body", "x"],
        )

    assert result.exit_code == 0
    assert "warning: comment targets outdated code" in result.output


def test_invalid_review_id():
    result = CliRunner().invoke(
        cli,
        ["comment", "--review-id", "BAD", "--path", "f.ts", "--line", "1", "--body", "x"],
    )

    assert result.exit_code == 1
    assert "invalid review id: BAD" in result.output


def test_gh_error():
    with patch(
        "gh_review.comment.gh_graphql_mutation",
        side_effect=GhError("server error"),
    ):
        result = CliRunner().invoke(
            cli,
            ["comment", "--review-id", "PRR_x", "--path", "f.ts", "--line", "1", "--body", "x"],
        )

    assert result.exit_code == 1
    assert "server error" in result.output


# -- file-level (explicit) ----------------------------------------------------


def test_explicit_file_level():
    resp = _thread_response(subject_type="FILE", line=None)
    with patch("gh_review.comment.gh_graphql_mutation", return_value=resp) as mock_gql:
        result = CliRunner().invoke(
            cli,
            ["comment", "--review-id", "PRR_x", "--path", "src/foo.ts", "--body", "file comment"],
        )

    assert result.exit_code == 0
    assert "line: file-level" in result.output
    mutation_input = mock_gql.call_args[0][1]["input"]
    assert mutation_input["subjectType"] == "FILE"
    assert "line" not in mutation_input
    assert "side" not in mutation_input


def test_explicit_file_level_not_in_diff():
    with patch("gh_review.comment.gh_graphql_mutation", return_value=_NULL_THREAD):
        result = CliRunner().invoke(
            cli,
            ["comment", "--review-id", "PRR_x", "--path", "missing.ts", "--body", "x"],
        )

    assert result.exit_code == 1
    assert "missing.ts is not in the PR diff" in result.output


# -- auto-fallback to file-level -----------------------------------------------


def test_line_outside_diff_falls_back_to_file():
    """Line comment gets thread:null, retry as file-level succeeds."""
    file_resp = _thread_response(subject_type="FILE", line=None)
    responses = [_NULL_THREAD, file_resp]

    with patch(
        "gh_review.comment.gh_graphql_mutation",
        side_effect=responses,
    ) as mock_gql:
        result = CliRunner().invoke(
            cli,
            [
                "comment",
                "--review-id",
                "PRR_x",
                "--path",
                "src/foo.ts",
                "--line",
                "999",
                "--body",
                "orphan comment",
            ],
        )

    assert result.exit_code == 0
    assert "line: file-level" in result.output
    assert "L999 was outside diff; posted as file-level comment" in result.output
    # First call: line-level, second call: file-level.
    assert mock_gql.call_count == 2
    first_input = mock_gql.call_args_list[0][0][1]["input"]
    second_input = mock_gql.call_args_list[1][0][1]["input"]
    assert first_input["subjectType"] == "LINE"
    assert second_input["subjectType"] == "FILE"


def test_line_outside_diff_range_falls_back_to_file():
    """Multi-line target outside diff falls back with correct note."""
    file_resp = _thread_response(subject_type="FILE", line=None)
    responses = [_NULL_THREAD, file_resp]

    with patch("gh_review.comment.gh_graphql_mutation", side_effect=responses):
        result = CliRunner().invoke(
            cli,
            [
                "comment",
                "--review-id",
                "PRR_x",
                "--path",
                "src/foo.ts",
                "--start-line",
                "100",
                "--line",
                "200",
                "--body",
                "range",
            ],
        )

    assert result.exit_code == 0
    assert "L100-200 was outside diff; posted as file-level comment" in result.output


def test_line_outside_diff_fallback_also_fails():
    """Both line and file-level fail (file not in diff at all)."""
    with patch(
        "gh_review.comment.gh_graphql_mutation",
        return_value=_NULL_THREAD,
    ):
        result = CliRunner().invoke(
            cli,
            ["comment", "--review-id", "PRR_x", "--path", "gone.ts", "--line", "50", "--body", "x"],
        )

    assert result.exit_code == 1
    assert "L50 is outside the diff" in result.output
    assert "gone.ts is not in the PR diff" in result.output


def test_line_outside_diff_fallback_gh_error():
    """Line fails with null thread, file-level retry raises GhError."""

    def side_effect(query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if variables["input"].get("subjectType") == "FILE":
            raise GhError("API down")
        return _NULL_THREAD

    with patch("gh_review.comment.gh_graphql_mutation", side_effect=side_effect):
        result = CliRunner().invoke(
            cli,
            [
                "comment",
                "--review-id",
                "PRR_x",
                "--path",
                "src/foo.ts",
                "--line",
                "50",
                "--body",
                "x",
            ],
        )

    assert result.exit_code == 1
    assert "file-level fallback failed" in result.output
