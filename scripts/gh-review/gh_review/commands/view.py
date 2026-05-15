"""View PR comments with filtering and LLM-optimized output."""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from typing import Any

from ..formatting import (
    format_conversation_comments,
    format_pending_reviews,
    format_review_threads,
)
from ..gh import gh_graphql, split_repo
from ..sanitize import is_bot

_VIEW_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          title
          author { login }
          reviews(first:50) {
            nodes {
              id state
              author { login }
            }
          }
          reviewThreads(first:100) {
            nodes {
              id isResolved isOutdated
              path line startLine
              comments(first:50) {
                nodes {
                  id databaseId
                  author { login __typename }
                  body createdAt
                  pullRequestReview { id state }
                }
              }
            }
          }
          comments(first:100) {
            nodes {
              id databaseId
              author { login __typename }
              body createdAt
            }
          }
        }
      }
    }""")


def _parse_iso(datestr: str) -> datetime:
    """Parse ISO 8601 date string to UTC datetime."""
    if datestr.endswith("Z"):
        datestr = datestr[:-1] + "+00:00"
    return datetime.fromisoformat(datestr)


def _thread_latest_date(thread: dict[str, Any]) -> datetime:
    """Get the most recent comment date in a thread."""
    comments = (thread.get("comments") or {}).get("nodes", [])
    if not comments:
        return datetime.min.replace(tzinfo=timezone.utc)
    dates = [_parse_iso(c["createdAt"]) for c in comments if c.get("createdAt")]
    return max(dates) if dates else datetime.min.replace(tzinfo=timezone.utc)


def _thread_last_author(thread: dict[str, Any]) -> str:
    """Get the login of the last commenter in a thread."""
    comments = (thread.get("comments") or {}).get("nodes", [])
    if not comments:
        return ""
    last = comments[-1]
    return (last.get("author") or {}).get("login", "")


def _filter_threads(
    threads: list[dict[str, Any]],
    *,
    show_all: bool,
    unanswered_by: str | None,
    since: datetime | None,
    no_bots: bool,
) -> list[dict[str, Any]]:
    result = []
    for t in threads:
        if not show_all and t.get("isResolved"):
            continue
        if since and _thread_latest_date(t) < since:
            continue
        if unanswered_by:
            last = _thread_last_author(t)
            if last == unanswered_by:
                continue
        if no_bots:
            comments = (t.get("comments") or {}).get("nodes", [])
            non_bot = [
                c
                for c in comments
                if not is_bot(
                    (c.get("author") or {}).get("login", ""),
                    (c.get("author") or {}).get("__typename", ""),
                )
            ]
            if not non_bot:
                continue
        result.append(t)
    return result


def _filter_conversation(
    comments: list[dict[str, Any]],
    *,
    since: datetime | None,
    no_bots: bool,
) -> list[dict[str, Any]]:
    result = []
    for c in comments:
        if since:
            created = _parse_iso(c.get("createdAt", ""))
            if created < since:
                continue
        author = c.get("author") or {}
        login = author.get("login", "")
        typename = author.get("__typename", "")
        if no_bots and is_bot(login, typename):
            continue
        result.append(c)
    return result


def run(
    repo: str,
    number: int,
    *,
    show_all: bool = False,
    unanswered: bool = False,
    since: datetime | None = None,
    no_bots: bool = False,
    max_body: int = 500,
) -> None:
    owner, name = split_repo(repo)
    data = gh_graphql(
        _VIEW_QUERY,
        owner=owner,
        repo=name,
        number=str(number),
    )
    pr = data["data"]["repository"]["pullRequest"]
    if not pr:
        from ..gh import die

        die(f"PR #{number} not found in {repo}")

    pr_author = (pr.get("author") or {}).get("login", "")
    title = pr.get("title", "")

    # Pending reviews
    all_reviews = pr.get("reviews", {}).get("nodes", [])
    pending = [r for r in all_reviews if r["state"] == "PENDING"]

    # Review threads
    all_threads = pr.get("reviewThreads", {}).get("nodes", [])
    threads = _filter_threads(
        all_threads,
        show_all=show_all,
        unanswered_by=pr_author if unanswered else None,
        since=since,
        no_bots=no_bots,
    )

    # Conversation comments
    all_convo = pr.get("comments", {}).get("nodes", [])
    convo = _filter_conversation(
        all_convo,
        since=since,
        no_bots=no_bots,
    )

    # Summary line
    total_threads = len(all_threads)
    unresolved_count = sum(1 for t in all_threads if not t.get("isResolved"))
    total_convo = len(all_convo)
    shown_threads = len(threads)
    shown_convo = len(convo)

    print(f"PR #{number}: {title}")
    print(
        f"{unresolved_count}/{total_threads} unresolved threads, "
        f"{shown_convo} conversation comments"
    )

    filter_notes: list[str] = []
    if show_all:
        filter_notes.append(f"showing all; {shown_threads} threads after filters")
    elif shown_threads < unresolved_count:
        filter_notes.append(
            f"{shown_threads} of {unresolved_count} unresolved threads after filters"
        )
    if shown_convo < total_convo:
        filter_notes.append(f"{shown_convo} of {total_convo} conversation comments after filters")
    if filter_notes:
        print(f"({'; '.join(filter_notes)})")

    # Pending reviews
    pending_out = format_pending_reviews(pending)
    if pending_out:
        print(f"\n{pending_out}")

    # Review threads
    print("\n--- review threads ---")
    print(format_review_threads(threads, max_body, no_bots))

    # Conversation comments
    print("\n--- conversation comments ---")
    print(format_conversation_comments(convo, max_body, no_bots))
