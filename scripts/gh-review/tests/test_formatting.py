"""Tests for prose output formatting."""

from __future__ import annotations

from gh_review._formatting import (
    format_conversation_comments,
    format_pending_reviews,
    format_review_bodies,
    format_review_threads,
)


def test_empty_threads():
    assert format_review_threads([], 500, False) == "no review threads"


def test_unresolved_thread():
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 42,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "reviewer"},
                        "body": "This looks wrong.",
                        "createdAt": "2026-05-13T10:00:00Z",
                        "databaseId": 98765,
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "[unresolved]" in result
    assert "src/main.ts L42" in result
    assert "@reviewer" in result
    assert "#98765" in result
    assert "This looks wrong." in result


def test_missing_database_id():
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 10,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "reviewer"},
                        "body": "No id here.",
                        "createdAt": "2026-05-13T10:00:00Z",
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "@reviewer (2026-05-13):" in result
    assert "#" not in result


def test_resolved_thread():
    threads = [
        {
            "isResolved": True,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 10,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "reviewer"},
                        "body": "Fixed.",
                        "createdAt": "2026-05-13T10:00:00Z",
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "[resolved]" in result


def test_multiline_range():
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 15,
            "startLine": 10,
            "comments": {"nodes": []},
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "L10-15" in result


def test_bot_comments_sanitized():
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 5,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "coderabbitai[bot]", "__typename": "Bot"},
                        "body": (
                            "Real finding.\n<details><summary>Junk</summary>Lots of stuff</details>"
                        ),
                        "createdAt": "2026-05-13T10:00:00Z",
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "[bot, sanitized]" in result
    assert "Real finding." in result
    assert "Junk" not in result


def test_bot_by_typename_sanitized():
    """Bots without [bot] suffix are detected via __typename."""
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 5,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "linear", "__typename": "Bot"},
                        "body": "Issue linked.\n<details><summary>Config</summary>stuff</details>",
                        "createdAt": "2026-05-13T10:00:00Z",
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "[bot, sanitized]" in result
    assert "Issue linked." in result
    assert "Config" not in result


def test_bot_comments_dropped_with_no_bots():
    threads = [
        {
            "isResolved": False,
            "isOutdated": False,
            "path": "src/main.ts",
            "line": 5,
            "startLine": None,
            "comments": {
                "nodes": [
                    {
                        "author": {"login": "coderabbitai[bot]", "__typename": "Bot"},
                        "body": "Bot says something.",
                        "createdAt": "2026-05-13T10:00:00Z",
                        "pullRequestReview": {"id": "PRR_1", "state": "COMMENTED"},
                    }
                ]
            },
        }
    ]
    result = format_review_threads(threads, 500, True)
    assert "coderabbitai" not in result


def test_outdated_flag():
    threads = [
        {
            "isResolved": False,
            "isOutdated": True,
            "path": "old.ts",
            "line": 1,
            "startLine": None,
            "comments": {"nodes": []},
        }
    ]
    result = format_review_threads(threads, 500, False)
    assert "outdated" in result


def test_conversation_empty():
    result = format_conversation_comments([], 500, False)
    assert result == "no conversation comments"


def test_human_comment():
    comments = [
        {
            "author": {"login": "rcdailey"},
            "body": "Looks good to me.",
            "createdAt": "2026-05-13T12:00:00Z",
            "databaseId": 55555,
        }
    ]
    result = format_conversation_comments(comments, 500, False)
    assert "@rcdailey" in result
    assert "#55555" in result
    assert "Looks good to me." in result


def test_bot_comment_sanitized():
    comments = [
        {
            "author": {"login": "linear", "__typename": "Bot"},
            "body": "Issue linked.\n<details><summary>Config</summary>blah</details>",
            "createdAt": "2026-05-13T12:00:00Z",
        }
    ]
    result = format_conversation_comments(comments, 500, False)
    assert "[bot, sanitized]" in result
    assert "Issue linked." in result
    assert "Config" not in result


def test_bot_dropped_with_no_bots():
    comments = [
        {
            "author": {"login": "linear", "__typename": "Bot"},
            "body": "Linked.",
            "createdAt": "2026-05-13T12:00:00Z",
        }
    ]
    result = format_conversation_comments(comments, 500, True)
    assert result == "no conversation comments"


def test_review_bodies_empty():
    assert format_review_bodies([], 500, False) == "no review comments"


def test_human_review_with_body():
    reviews = [
        {
            "author": {"login": "reviewer", "__typename": "User"},
            "body": "High level feedback here.",
            "createdAt": "2026-05-16T10:00:00Z",
            "databaseId": 12345,
            "state": "COMMENTED",
        }
    ]
    result = format_review_bodies(reviews, 500, False)
    assert "@reviewer" in result
    assert "[commented]" in result
    assert "#12345" in result
    assert "High level feedback here." in result


def test_bot_review_sanitized():
    reviews = [
        {
            "author": {"login": "sourcery-ai[bot]", "__typename": "Bot"},
            "body": "Feedback.\n<details><summary>Prompt</summary>stuff</details>",
            "createdAt": "2026-05-16T10:00:00Z",
            "databaseId": 99999,
            "state": "COMMENTED",
        }
    ]
    result = format_review_bodies(reviews, 500, False)
    assert "[bot, sanitized]" in result
    assert "Feedback." in result
    assert "Prompt" not in result


def test_bot_review_dropped_with_no_bots():
    reviews = [
        {
            "author": {"login": "sourcery-ai[bot]", "__typename": "Bot"},
            "body": "Feedback.",
            "createdAt": "2026-05-16T10:00:00Z",
            "state": "COMMENTED",
        }
    ]
    result = format_review_bodies(reviews, 500, True)
    assert result == "no review comments"


def test_approved_state_shown():
    reviews = [
        {
            "author": {"login": "reviewer"},
            "body": "LGTM",
            "createdAt": "2026-05-16T10:00:00Z",
            "state": "APPROVED",
        }
    ]
    result = format_review_bodies(reviews, 500, False)
    assert "[approved]" in result


def test_pending_reviews_empty():
    assert format_pending_reviews([]) == ""


def test_pending_reviews_with_pending():
    reviews = [{"id": "PRR_abc123", "author": {"login": "me"}}]
    result = format_pending_reviews(reviews)
    assert "PENDING REVIEWS" in result
    assert "PRR_abc123" in result
    assert "@me" in result
