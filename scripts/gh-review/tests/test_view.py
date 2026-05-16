"""Tests for the view command's summary and filter notes."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from gh_review.cli import cli


def _make_pr_data(
    threads: list[dict[str, Any]] | None = None,
    convo: list[dict[str, Any]] | None = None,
    reviews: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal GraphQL response for the view command."""
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "title": "test pr",
                    "author": {"login": "author"},
                    "reviews": {"nodes": reviews or []},
                    "reviewThreads": {"nodes": threads or []},
                    "comments": {"nodes": convo or []},
                }
            }
        }
    }


def _bot_thread(resolved: bool = False) -> dict[str, Any]:
    return {
        "id": "T1",
        "isResolved": resolved,
        "isOutdated": False,
        "path": "src/main.ts",
        "line": 10,
        "startLine": None,
        "comments": {
            "nodes": [
                {
                    "id": "C1",
                    "databaseId": 111,
                    "author": {"login": "coderabbitai[bot]", "__typename": "Bot"},
                    "body": "Bot finding.",
                    "createdAt": "2026-05-14T10:00:00Z",
                    "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                }
            ]
        },
    }


def _human_thread() -> dict[str, Any]:
    return {
        "id": "T2",
        "isResolved": False,
        "isOutdated": False,
        "path": "src/other.ts",
        "line": 20,
        "startLine": None,
        "comments": {
            "nodes": [
                {
                    "id": "C2",
                    "databaseId": 222,
                    "author": {"login": "reviewer", "__typename": "User"},
                    "body": "Please fix this.",
                    "createdAt": "2026-05-14T11:00:00Z",
                    "pullRequestReview": {"id": "PRR_2", "state": "COMMENTED"},
                }
            ]
        },
    }


def _bot_convo() -> dict[str, Any]:
    return {
        "id": "IC1",
        "databaseId": 333,
        "author": {"login": "coderabbitai[bot]", "__typename": "Bot"},
        "body": "Walkthrough summary.",
        "createdAt": "2026-05-14T10:00:00Z",
    }


def _human_convo() -> dict[str, Any]:
    return {
        "id": "IC2",
        "databaseId": 444,
        "author": {"login": "reviewer", "__typename": "User"},
        "body": "Ship it.",
        "createdAt": "2026-05-14T12:00:00Z",
    }


def _review_with_body() -> dict[str, Any]:
    return {
        "id": "PRR_123",
        "databaseId": 4303794833,
        "state": "COMMENTED",
        "author": {"login": "sourcery-ai[bot]", "__typename": "Bot"},
        "body": "High level feedback.",
        "createdAt": "2026-05-16T10:00:00Z",
    }


def _review_no_body() -> dict[str, Any]:
    return {
        "id": "PRR_456",
        "databaseId": 789,
        "state": "APPROVED",
        "author": {"login": "reviewer", "__typename": "User"},
        "body": "",
        "createdAt": "2026-05-16T11:00:00Z",
    }


def test_no_bots_shows_thread_and_convo_filter_notes():
    """--no-bots with bot-only threads and bot convo shows both filter notes."""
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(
            threads=[_bot_thread(), _bot_thread()],
            convo=[_bot_convo(), _human_convo()],
        )
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1", "--no-bots"])

    assert result.exit_code == 0
    assert "0 of 2 unresolved threads after filters" in result.output
    assert "1 of 2 conversation comments after filters" in result.output


def test_no_filter_note_when_nothing_filtered():
    """No parenthetical when all items pass filters."""
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(
            threads=[_human_thread()],
            convo=[_human_convo()],
        )
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1"])

    assert result.exit_code == 0
    assert "after filters" not in result.output


def test_convo_only_filter_note():
    """Filter note only for convo when threads are unaffected."""
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(
            threads=[_human_thread()],
            convo=[_bot_convo()],
        )
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1", "--no-bots"])

    assert result.exit_code == 0
    assert "unresolved threads after filters" not in result.output
    assert "0 of 1 conversation comments after filters" in result.output


def test_show_all_combined_with_convo_filter():
    """--all + --no-bots: thread note uses 'showing all', convo note present."""
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(
            threads=[_bot_thread(), _human_thread()],
            convo=[_bot_convo()],
        )
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1", "--all", "--no-bots"])

    assert result.exit_code == 0
    assert "showing all; 1 threads after filters" in result.output
    assert "0 of 1 conversation comments after filters" in result.output


def test_review_body_shown():
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(reviews=[_review_with_body()])
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1"])

    assert result.exit_code == 0
    assert "--- review comments ---" in result.output
    assert "High level feedback." in result.output
    assert "#4303794833" in result.output


def test_review_body_hidden_when_empty():
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(reviews=[_review_no_body()])
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1"])

    assert result.exit_code == 0
    assert "--- review comments ---" not in result.output


def test_review_body_dropped_with_no_bots():
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(reviews=[_review_with_body()])
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1", "--no-bots"])

    assert result.exit_code == 0
    assert "--- review comments ---" not in result.output
    assert "High level feedback." not in result.output


def test_thread_comment_shows_database_id():
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(threads=[_human_thread()])
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1"])

    assert result.exit_code == 0
    assert "#222" in result.output


def test_convo_comment_shows_database_id():
    with patch("gh_review.view.gh_graphql") as mock_gql:
        mock_gql.return_value = _make_pr_data(convo=[_human_convo()])
        result = CliRunner().invoke(cli, ["view", "owner/repo", "1"])

    assert result.exit_code == 0
    assert "#444" in result.output
