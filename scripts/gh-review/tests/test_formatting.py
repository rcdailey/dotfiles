"""Tests for prose output formatting."""

from gh_review.formatting import (
    format_conversation_comments,
    format_pending_reviews,
    format_review_threads,
)


class TestFormatReviewThreads:
    def test_empty_threads(self):
        assert format_review_threads([], 500, False) == "no review threads"

    def test_unresolved_thread(self):
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
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
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

    def test_missing_database_id(self):
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
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
                        }
                    ]
                },
            }
        ]
        result = format_review_threads(threads, 500, False)
        assert "@reviewer (2026-05-13):" in result
        assert "#" not in result

    def test_resolved_thread(self):
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
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
                        }
                    ]
                },
            }
        ]
        result = format_review_threads(threads, 500, False)
        assert "[resolved]" in result

    def test_multiline_range(self):
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

    def test_bot_comments_sanitized(self):
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
                            "author": {
                                "login": "coderabbitai[bot]",
                                "__typename": "Bot",
                            },
                            "body": (
                                "Real finding.\n"
                                "<details><summary>Junk</summary>"
                                "Lots of stuff</details>"
                            ),
                            "createdAt": "2026-05-13T10:00:00Z",
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
                        }
                    ]
                },
            }
        ]
        result = format_review_threads(threads, 500, False)
        assert "[bot, sanitized]" in result
        assert "Real finding." in result
        assert "Junk" not in result

    def test_bot_by_typename_sanitized(self):
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
                            "author": {
                                "login": "linear",
                                "__typename": "Bot",
                            },
                            "body": (
                                "Issue linked.\n<details><summary>Config</summary>stuff</details>"
                            ),
                            "createdAt": "2026-05-13T10:00:00Z",
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
                        }
                    ]
                },
            }
        ]
        result = format_review_threads(threads, 500, False)
        assert "[bot, sanitized]" in result
        assert "Issue linked." in result
        assert "Config" not in result

    def test_bot_comments_dropped_with_no_bots(self):
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
                            "author": {
                                "login": "coderabbitai[bot]",
                                "__typename": "Bot",
                            },
                            "body": "Bot says something.",
                            "createdAt": "2026-05-13T10:00:00Z",
                            "pullRequestReview": {
                                "id": "PRR_1",
                                "state": "COMMENTED",
                            },
                        }
                    ]
                },
            }
        ]
        result = format_review_threads(threads, 500, True)
        assert "coderabbitai" not in result

    def test_outdated_flag(self):
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


class TestFormatConversationComments:
    def test_empty(self):
        result = format_conversation_comments([], 500, False)
        assert result == "no conversation comments"

    def test_human_comment(self):
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

    def test_bot_comment_sanitized(self):
        comments = [
            {
                "author": {
                    "login": "linear",
                    "__typename": "Bot",
                },
                "body": ("Issue linked.\n<details><summary>Config</summary>blah</details>"),
                "createdAt": "2026-05-13T12:00:00Z",
            }
        ]
        result = format_conversation_comments(comments, 500, False)
        assert "[bot, sanitized]" in result
        assert "Issue linked." in result
        assert "Config" not in result

    def test_bot_dropped_with_no_bots(self):
        comments = [
            {
                "author": {
                    "login": "linear",
                    "__typename": "Bot",
                },
                "body": "Linked.",
                "createdAt": "2026-05-13T12:00:00Z",
            }
        ]
        result = format_conversation_comments(comments, 500, True)
        assert result == "no conversation comments"


class TestFormatPendingReviews:
    def test_empty(self):
        assert format_pending_reviews([]) == ""

    def test_with_pending(self):
        reviews = [
            {"id": "PRR_abc123", "author": {"login": "me"}},
        ]
        result = format_pending_reviews(reviews)
        assert "PENDING REVIEWS" in result
        assert "PRR_abc123" in result
        assert "@me" in result
