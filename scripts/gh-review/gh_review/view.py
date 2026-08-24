"""View PR comments with filtering and LLM-optimized output."""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from typing import Any

import click

from gh_review._duration import parse_duration
from gh_review._errors import GhError, die
from gh_review._formatting import (
    format_conversation_comments,
    format_pending_reviews,
    format_reviews,
)
from gh_review._gh import gh_graphql, split_repo
from gh_review._sanitize import is_bot

DEFAULT_MAX_BODY = 1500

_VIEW_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          title
          author { login }
          reviews(first:50) {
            nodes {
              id databaseId state
              author { login __typename }
              body createdAt
              comments(first:50) {
                nodes {
                  id databaseId
                  path line startLine
                  body createdAt
                }
              }
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


class _DurationType(click.ParamType):
    """Click param type that parses relative duration strings."""

    name = "DURATION"

    def convert(
        self, value: str | datetime, param: click.Parameter | None, ctx: click.Context | None
    ) -> datetime:
        if isinstance(value, datetime):
            return value
        try:
            return parse_duration(value)
        except ValueError as e:
            self.fail(str(e), param, ctx)


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


def _login(node: dict[str, Any]) -> str:
    return (node.get("author") or {}).get("login", "")


def _filter_threads(
    threads: list[dict[str, Any]],
    *,
    show_all: bool,
    unanswered_by: str | None,
    since: datetime | None,
    no_bots: bool,
    author: str | None,
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
        if author:
            comments = (t.get("comments") or {}).get("nodes", [])
            by_author = [c for c in comments if _login(c) == author]
            if not by_author:
                continue
            t = {**t, "comments": {"nodes": by_author}}
        result.append(t)
    return result


def _filter_conversation(
    comments: list[dict[str, Any]],
    *,
    since: datetime | None,
    no_bots: bool,
    author: str | None,
) -> list[dict[str, Any]]:
    result = []
    for c in comments:
        if author and _login(c) != author:
            continue
        if since:
            created = _parse_iso(c.get("createdAt", ""))
            if created < since:
                continue
        comment_author = c.get("author") or {}
        login = comment_author.get("login", "")
        typename = comment_author.get("__typename", "")
        if no_bots and is_bot(login, typename):
            continue
        result.append(c)
    return result


def _filter_review_bodies(
    reviews: list[dict[str, Any]],
    *,
    since: datetime | None,
    no_bots: bool,
    author: str | None,
) -> list[dict[str, Any]]:
    """Filter submitted reviews whose body should be shown."""
    result = []
    for r in reviews:
        if r.get("state") == "PENDING":
            continue
        if author and _login(r) != author:
            continue
        if since:
            created = _parse_iso(r.get("createdAt", ""))
            if created < since:
                continue
        review_author = r.get("author") or {}
        login = review_author.get("login", "")
        typename = review_author.get("__typename", "")
        if no_bots and is_bot(login, typename):
            continue
        result.append(r)
    return result


def _group_reviews(
    reviews: list[dict[str, Any]],
    shown_review_ids: set[str],
    threads: list[dict[str, Any]],
) -> list[tuple[dict[str, Any] | None, list[dict[str, Any]]]]:
    """Attach each thread to the review that created it, preserving review order."""
    by_review: dict[str, list[dict[str, Any]]] = {}
    orphans: list[dict[str, Any]] = []
    for t in threads:
        comments = (t.get("comments") or {}).get("nodes", [])
        first = comments[0] if comments else {}
        review_id = (first.get("pullRequestReview") or {}).get("id")
        if review_id:
            by_review.setdefault(review_id, []).append(t)
            continue
        orphans.append(t)

    groups: list[tuple[dict[str, Any] | None, list[dict[str, Any]]]] = []
    for r in reviews:
        review = r if r.get("id") in shown_review_ids else {**r, "body": ""}
        groups.append((review, by_review.get(r.get("id"), [])))
    if orphans:
        groups.append((None, orphans))
    return groups


@click.command()
@click.argument("repo")
@click.argument("number", type=int)
@click.option("--all", "show_all", is_flag=True, help="show all threads (default: unresolved only)")
@click.option(
    "--unanswered", is_flag=True, help="only threads where PR author has not replied last"
)
@click.option(
    "--since",
    type=_DurationType(),
    default=None,
    metavar="DURATION",
    help="relative time filter (e.g. 1h, 2d, 1w)",
)
@click.option("--no-bots", is_flag=True, help="drop bot comments entirely")
@click.option(
    "--author",
    default=None,
    metavar="LOGIN",
    help="only comments authored by this login",
)
@click.option(
    "--max-body",
    type=int,
    default=DEFAULT_MAX_BODY,
    metavar="N",
    show_default=True,
    help="max comment body length",
)
def cli(
    repo: str,
    number: int,
    show_all: bool,
    unanswered: bool,
    since: datetime | None,
    no_bots: bool,
    author: str | None,
    max_body: int,
) -> None:
    """View PR comments with filtering and LLM-optimized output."""
    try:
        owner, name = split_repo(repo)
        data = gh_graphql(
            _VIEW_QUERY,
            owner=owner,
            repo=name,
            number=str(number),
        )
        pr = data["data"]["repository"]["pullRequest"]
        if not pr:
            die(f"PR #{number} not found in {repo}")

        pr_author = (pr.get("author") or {}).get("login", "")
        title = pr.get("title", "")

        # Reviews
        all_reviews = pr.get("reviews", {}).get("nodes", [])
        pending = [
            r
            for r in all_reviews
            if r["state"] == "PENDING" and (not author or _login(r) == author)
        ]
        review_bodies = _filter_review_bodies(
            all_reviews,
            since=since,
            no_bots=no_bots,
            author=author,
        )

        # Review threads
        all_threads = pr.get("reviewThreads", {}).get("nodes", [])
        threads = _filter_threads(
            all_threads,
            show_all=show_all,
            unanswered_by=pr_author if unanswered else None,
            since=since,
            no_bots=no_bots,
            author=author,
        )

        # Conversation comments
        all_convo = pr.get("comments", {}).get("nodes", [])
        convo = _filter_conversation(
            all_convo,
            since=since,
            no_bots=no_bots,
            author=author,
        )

        # Summary line
        total_threads = len(all_threads)
        unresolved_count = sum(1 for t in all_threads if not t.get("isResolved"))
        total_convo = len(all_convo)
        shown_threads = len(threads)
        shown_convo = len(convo)

        if not total_threads:
            thread_summary = "no review threads exist"
        elif not unresolved_count:
            thread_summary = f"0/{total_threads} unresolved threads (all resolved)"
        else:
            thread_summary = f"{unresolved_count}/{total_threads} unresolved threads"

        click.echo(f"PR #{number}: {title}")
        click.echo(f"{thread_summary}, {shown_convo} conversation comments")

        filter_notes: list[str] = []
        if show_all:
            filter_notes.append(f"showing all; {shown_threads} threads after filters")
        elif shown_threads < unresolved_count:
            filter_notes.append(
                f"{shown_threads} of {unresolved_count} unresolved threads after filters"
            )
        if shown_convo < total_convo:
            filter_notes.append(
                f"{shown_convo} of {total_convo} conversation comments after filters"
            )
        if filter_notes:
            click.echo(f"({'; '.join(filter_notes)})")

        # Pending reviews
        pending_out = format_pending_reviews(pending, max_body)
        if pending_out:
            click.echo(f"\n{pending_out}")

        # Reviews, each with its inline threads nested underneath
        submitted = [r for r in all_reviews if r.get("state") != "PENDING"]
        shown_review_ids = {r.get("id") for r in review_bodies if r.get("id")}
        click.echo("\n--- reviews ---\n")
        click.echo(
            format_reviews(_group_reviews(submitted, shown_review_ids, threads), max_body, no_bots)
        )

        # Conversation comments
        click.echo("\n--- conversation comments ---\n")
        click.echo(format_conversation_comments(convo, max_body, no_bots))

    except GhError as exc:
        die(str(exc))
