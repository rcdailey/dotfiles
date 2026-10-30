import os
import time
import unittest
from unittest import mock

from click.testing import CliRunner
from gh_review import responses

SINCE = "2026-10-29T00:00:00Z"


def setUpModule() -> None:
    os.environ["TZ"] = "UTC"
    time.tzset()


def _comment(cid, login, created, body, reactions=(), typename="User"):
    return {
        "id": cid,
        "body": body,
        "createdAt": created,
        "author": {"login": login, "__typename": typename},
        "reactions": {
            "nodes": [{"content": c, "createdAt": t, "user": {"login": u}} for c, t, u in reactions]
        },
    }


def _pr(threads, comments=()):
    return {
        "id": "PR_1",
        "number": 7,
        "title": "Scope bundles",
        "body": "Scopes bundles to the selected program.",
        "repository": {"nameWithOwner": "acme/api"},
        "author": {"login": "alice"},
        "reviewThreads": {"nodes": [{"path": "a.ts", "comments": {"nodes": t}} for t in threads]},
        "comments": {"nodes": list(comments)},
        "reviews": {"nodes": []},
    }


def _reply_review(reply_to):
    return {
        "__typename": "PullRequestReview",
        "author": {"login": "alice"},
        "state": "COMMENTED",
        "body": "",
        "comments": {"nodes": [{"replyTo": {"id": reply_to}}]},
    }


def _run(pr, timeline=(), notified=True):
    def graphql(query, variables):
        if "search(" in query:
            return {
                "data": {"search": {"pageInfo": {"hasNextPage": False}, "nodes": [{"id": "PR_1"}]}}
            }
        if "viewer" in query:
            return {"data": {"viewer": {"login": "me"}}}
        if "nodes(ids" in query:
            return {"data": {"nodes": [pr]}}
        return {
            "data": {
                "p0": {
                    "timelineItems": {"pageInfo": {"hasNextPage": False}, "nodes": list(timeline)}
                }
            }
        }

    notifications = [
        {
            "id": "900",
            "last_read_at": SINCE,
            "subject": {
                "type": "PullRequest",
                "url": "https://api.github.com/repos/acme/api/pulls/7",
            },
            "repository": {"full_name": "acme/api"},
        }
    ]
    with (
        mock.patch.object(responses, "gh_graphql_mutation", side_effect=graphql),
        mock.patch.object(
            responses, "gh_rest_pages", return_value=notifications if notified else []
        ),
        mock.patch.object(responses, "load_checked", return_value=SINCE),
    ):
        result = CliRunner().invoke(responses.cli, ["show", "--org", "acme"])
    assert result.exit_code == 0, result.output
    return result.output


class ShowTest(unittest.TestCase):
    def test_reports_new_human_reply_to_your_thread_comment(self) -> None:
        out = _run(
            _pr(
                [
                    [
                        _comment("C1", "me", "2026-10-28T00:00:00Z", "Should this be cached?"),
                        _comment("C2", "alice", "2026-10-28T12:00:00Z", "Old reply"),
                        _comment(
                            "C3",
                            "coderabbitai",
                            "2026-10-29T01:00:00Z",
                            "Bot noise",
                            typename="Bot",
                        ),
                        _comment("C4", "alice", "2026-10-29T02:00:00Z", "Cached it now"),
                    ]
                ]
            )
        )
        self.assertIn("acme/api#7 by alice: Scope bundles", out)
        self.assertIn("- Your thread on a.ts: Should this be cached?", out)
        self.assertIn("  2:00 AM alice replied: Cached it now", out)
        self.assertNotIn("Old reply", out)
        self.assertNotIn("Bot noise", out)

    def test_reports_others_new_reactions_as_emoji(self) -> None:
        mine = _comment(
            "C1",
            "me",
            "2026-10-28T00:00:00Z",
            "LGTM overall",
            reactions=[
                ("THUMBS_UP", "2026-10-29T03:00:00Z", "alice"),
                ("HEART", "2026-10-29T03:00:00Z", "me"),
                ("ROCKET", "2026-10-28T03:00:00Z", "bob"),
            ],
        )
        out = _run(_pr([], comments=[mine]))
        self.assertIn("- Your conversation comment: LGTM overall", out)
        self.assertIn("  3:00 AM \U0001f44d alice\n", out)
        self.assertNotIn("bob", out)

    def test_groups_responses_by_local_day_newest_first(self) -> None:
        out = _run(
            _pr(
                [
                    [
                        _comment("C1", "me", "2026-10-28T00:00:00Z", "Question"),
                        _comment("C2", "alice", "2026-10-29T08:00:00Z", "First answer"),
                        _comment("C3", "alice", "2026-10-30T09:00:00Z", "Second answer"),
                    ]
                ]
            )
        )
        newer = out.index(", Friday Oct 30\n")
        older = out.index(", Thursday Oct 29\n")
        self.assertLess(newer, out.index("Second answer"))
        self.assertLess(out.index("Second answer"), older)
        self.assertLess(older, out.index("First answer"))

    def test_omits_prs_without_new_responses(self) -> None:
        out = _run(_pr([[_comment("C1", "me", "2026-10-29T05:00:00Z", "Nit")]]))
        self.assertIn("No new replies or reactions.", out)
        self.assertNotIn("acme/api#7", out)

    def test_marks_read_when_only_replies_to_you_arrived(self) -> None:
        pr = _pr(
            [
                [
                    _comment("C1", "me", "2026-10-28T00:00:00Z", "Question"),
                    _comment("C2", "alice", "2026-10-29T02:00:00Z", "Answer"),
                ]
            ]
        )
        out = _run(pr, timeline=[_reply_review("C1"), {"__typename": "LabeledEvent"}])
        self.assertIn("Mark read: acme/api#7.", out)
        self.assertIn("ack --org acme --until ", out)
        self.assertIn("--read 900", out)

    def test_leaves_unread_when_other_activity_arrived(self) -> None:
        pr = _pr(
            [
                [
                    _comment("C1", "me", "2026-10-28T00:00:00Z", "Question"),
                    _comment("C2", "alice", "2026-10-29T02:00:00Z", "Answer"),
                ]
            ]
        )
        commit = {
            "__typename": "PullRequestCommit",
            "commit": {"author": {"user": {"login": "alice"}}},
        }
        out = _run(pr, timeline=[_reply_review("C1"), commit, _reply_review("OTHER")])
        self.assertIn(
            "Leave unread acme/api#7: other activity (1 PullRequestCommit, 1 PullRequestReview).",
            out,
        )
        self.assertNotIn("--read", out)


class AckTest(unittest.TestCase):
    def test_marks_threads_read_then_saves_checked_time(self) -> None:
        with (
            mock.patch.object(responses, "gh_rest_json") as rest,
            mock.patch.object(responses, "save_checked") as save,
        ):
            result = CliRunner().invoke(
                responses.cli,
                [
                    "ack",
                    "--exclude-org",
                    "Acme",
                    "--until",
                    "2026-10-30T00:00:00Z",
                    "--read",
                    "1,2",
                ],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        rest.assert_has_calls(
            [
                mock.call("PATCH", "notifications/threads/1"),
                mock.call("PATCH", "notifications/threads/2"),
            ]
        )
        save.assert_called_once_with("not:acme", "2026-10-30T00:00:00Z")

    def test_rejects_malformed_until(self) -> None:
        with mock.patch.object(responses, "save_checked") as save:
            result = CliRunner().invoke(responses.cli, ["ack", "--until", "yesterday"])
        self.assertEqual(result.exit_code, 2)
        save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
