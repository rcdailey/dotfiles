import unittest
from unittest import mock

from click.testing import CliRunner
from gh_review import view

# A submitted bot review whose body groups a finding by file and line range, plus one inline thread.
PR_DATA = {
    "data": {
        "repository": {
            "pullRequest": {
                "title": "Resolve partners",
                "author": {"login": "robert"},
                "reviews": {
                    "nodes": [
                        {
                            "id": "PRR_review",
                            "databaseId": 111,
                            "state": "COMMENTED",
                            "author": {"login": "reviewer", "__typename": "User"},
                            "body": "Other comments\npartner-resolver.ts `22-26`: guard nulls",
                            "createdAt": "2026-10-01T00:00:00Z",
                            "comments": {"nodes": []},
                        }
                    ]
                },
                "reviewThreads": {
                    "nodes": [
                        {
                            "id": "PRRT_thread",
                            "isResolved": False,
                            "isOutdated": False,
                            "path": "partner-resolver.ts",
                            "line": 40,
                            "startLine": None,
                            "comments": {
                                "nodes": [
                                    {
                                        "id": "PRRC_comment",
                                        "databaseId": 222,
                                        "author": {"login": "reviewer", "__typename": "User"},
                                        "body": "inline finding",
                                        "createdAt": "2026-10-01T00:00:00Z",
                                        "pullRequestReview": {
                                            "id": "PRR_review",
                                            "state": "COMMENTED",
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
                "comments": {
                    "nodes": [
                        {
                            "id": "IC_comment",
                            "databaseId": 333,
                            "author": {"login": "linear", "__typename": "Bot"},
                            "body": "Review in Linear",
                            "createdAt": "2026-10-01T00:00:00Z",
                        }
                    ]
                },
            }
        }
    }
}


class ViewReviewBodyTest(unittest.TestCase):
    def _run(self) -> str:
        with mock.patch.object(view, "gh_graphql", return_value=PR_DATA):
            result = CliRunner().invoke(view.cli, ["owner/repo", "7"])
        self.assertEqual(result.exit_code, 0, result.output)
        return result.output

    def test_review_body_is_marked_unreplyable_and_has_no_reply_id(self) -> None:
        output = self._run()

        header = next(line for line in output.splitlines() if line.startswith("@reviewer"))
        self.assertIn("review body, no reply thread", header)
        self.assertNotIn("#111", output)

    def test_conversation_comment_has_no_reply_id(self) -> None:
        output = self._run()

        self.assertIn("Review in Linear", output)
        self.assertNotIn("#333", output)

    def test_thread_comment_keeps_reply_id(self) -> None:
        output = self._run()

        self.assertIn("#222 PRRC_comment", output)


if __name__ == "__main__":
    unittest.main()
