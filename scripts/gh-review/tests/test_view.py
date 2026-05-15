"""Tests for the view command's summary and filter notes."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from gh_review.commands.view import run


def _make_pr_data(
    threads: list[dict[str, Any]] | None = None,
    convo: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal GraphQL response for view.run()."""
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "title": "test pr",
                    "author": {"login": "author"},
                    "reviews": {"nodes": []},
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


class TestViewFilterNotes:
    @patch("gh_review.commands.view.gh_graphql")
    def test_no_bots_shows_thread_and_convo_filter_notes(self, mock_gql, capsys):
        """--no-bots with bot-only threads and bot convo shows both filter notes."""
        mock_gql.return_value = _make_pr_data(
            threads=[_bot_thread(), _bot_thread()],
            convo=[_bot_convo(), _human_convo()],
        )
        run("owner/repo", 1, no_bots=True)
        output = capsys.readouterr().out

        assert "0 of 2 unresolved threads after filters" in output
        assert "1 of 2 conversation comments after filters" in output

    @patch("gh_review.commands.view.gh_graphql")
    def test_no_filter_note_when_nothing_filtered(self, mock_gql, capsys):
        """No parenthetical when all items pass filters."""
        mock_gql.return_value = _make_pr_data(
            threads=[_human_thread()],
            convo=[_human_convo()],
        )
        run("owner/repo", 1)
        output = capsys.readouterr().out

        # No filter note line
        assert "after filters" not in output

    @patch("gh_review.commands.view.gh_graphql")
    def test_convo_only_filter_note(self, mock_gql, capsys):
        """Filter note only for convo when threads are unaffected."""
        mock_gql.return_value = _make_pr_data(
            threads=[_human_thread()],
            convo=[_bot_convo()],
        )
        run("owner/repo", 1, no_bots=True)
        output = capsys.readouterr().out

        assert "unresolved threads after filters" not in output
        assert "0 of 1 conversation comments after filters" in output

    @patch("gh_review.commands.view.gh_graphql")
    def test_show_all_combined_with_convo_filter(self, mock_gql, capsys):
        """--all + --no-bots: thread note uses 'showing all', convo note present."""
        mock_gql.return_value = _make_pr_data(
            threads=[_bot_thread(), _human_thread()],
            convo=[_bot_convo()],
        )
        run("owner/repo", 1, show_all=True, no_bots=True)
        output = capsys.readouterr().out

        assert "showing all; 1 threads after filters" in output
        assert "0 of 1 conversation comments after filters" in output


class TestViewDatabaseIds:
    @patch("gh_review.commands.view.gh_graphql")
    def test_thread_comment_shows_database_id(self, mock_gql, capsys):
        mock_gql.return_value = _make_pr_data(threads=[_human_thread()])
        run("owner/repo", 1)
        output = capsys.readouterr().out

        assert "#222" in output

    @patch("gh_review.commands.view.gh_graphql")
    def test_convo_comment_shows_database_id(self, mock_gql, capsys):
        mock_gql.return_value = _make_pr_data(convo=[_human_convo()])
        run("owner/repo", 1)
        output = capsys.readouterr().out

        assert "#444" in output
