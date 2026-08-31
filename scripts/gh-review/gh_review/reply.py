"""Reply to a PR review comment thread as part of a pending review."""

from __future__ import annotations

import json
import textwrap
from typing import Any

import click

from gh_review._body import body_option, read_body
from gh_review._click import RepoCommand
from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql, gh_graphql_mutation, gh_rest, split_repo
from gh_review._review import pending_reviews

_CONTEXT_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          reviews(first:50, states:[PENDING]) { nodes { id } }
          reviewThreads(first:100) {
            nodes { id comments(first:100) { nodes { databaseId } } }
          }
        }
      }
    }""")

_REPLY_MUTATION = textwrap.dedent("""\
    mutation($input: AddPullRequestReviewThreadReplyInput!) {
      addPullRequestReviewThreadReply(input: $input) {
        comment { databaseId url pullRequestReview { id state } }
      }
    }""")


def _fetch_context(repo: str, number: int) -> tuple[list[str], list[dict[str, Any]]]:
    """Return (pending review ids, review threads) for a pull request."""
    owner, name = split_repo(repo)
    data = gh_graphql(_CONTEXT_QUERY, owner=owner, repo=name, number=str(number))
    pr = data["data"]["repository"]["pullRequest"]
    if not pr:
        die(f"PR #{number} not found in {repo}")
    pending = [r["id"] for r in pr["reviews"]["nodes"]]
    return pending, pr["reviewThreads"]["nodes"]


def _find_thread(threads: list[dict[str, Any]], comment_id: int) -> str | None:
    """Return the node id of the thread containing a comment database id."""
    for thread in threads:
        for comment in (thread.get("comments") or {}).get("nodes", []):
            if comment.get("databaseId") == comment_id:
                return thread["id"]
    return None


def _has_pending(repo: str, number: int) -> bool:
    """Report whether a pending review exists, treating lookup failure as none."""
    try:
        return bool(pending_reviews(repo, number))
    except GhError:
        return False


def _reply_now(repo: str, number: int, comment_id: int, body: str) -> None:
    """Post a threaded reply immediately, outside any pending review."""
    try:
        raw = gh_rest(
            "POST",
            f"repos/{repo}/pulls/{number}/comments/{comment_id}/replies",
            body={"body": body},
            jq="{id, node_id, html_url}",
        )
    except GhError as exc:
        if exc.status == 404:
            die(
                f"comment {comment_id} is not a review comment on {repo}#{number} "
                "(conversation comments do not support threaded replies)"
            )
        if exc.status == 422 and _has_pending(repo, number):
            die(
                f"cannot publish a reply while you have a pending review on {repo}#{number}; "
                f"discard it with `gh-review delete {repo} {number}`, or drop --publish to "
                "attach the reply to it"
            )
        die(f"failed to post reply: {exc}")
    data = json.loads(raw)
    click.echo(f"id: {data['id']}")
    click.echo(f"node-id: {data['node_id']}")
    click.echo(f"url: {data['html_url']}")
    click.echo("state: PUBLISHED")


@click.command(cls=RepoCommand)
@click.argument("repo", metavar="[REPO]")
@click.argument("number", type=int)
@click.argument("comment_id", type=int)
@body_option(required=True)
@click.option(
    "--review-id",
    default=None,
    help="PRR_... node id; defaults to the existing pending review",
)
@click.option(
    "--publish",
    is_flag=True,
    help="post the reply immediately instead of attaching it to a pending review",
)
def cli(
    repo: str,
    number: int,
    comment_id: int,
    body: str,
    review_id: str | None,
    publish: bool,
) -> None:
    """Reply to a review comment thread on a pending review.

    The reply stays unsubmitted until the pending review is submitted, so it is
    invisible to everyone else until then. Requires a pending review to attach
    to; start one with `gh-review start` first.

    Pass --publish instead when answering a bot review on the user's own PR:
    there is no review for the user to submit, so batching buys nothing.
    """
    body = read_body(body)
    if body is None:
        die("--body is required")

    if publish:
        if review_id:
            die("--publish cannot be combined with --review-id")
        _reply_now(repo, number, comment_id, body)
        return

    if review_id and not review_id.startswith("PRR_"):
        die(f"invalid review id: {review_id} (expected PRR_... node id)")

    try:
        pending, threads = _fetch_context(repo, number)
    except GhError as exc:
        die(str(exc))

    thread_id = _find_thread(threads, comment_id)
    if thread_id is None:
        die(
            f"comment {comment_id} is not a review comment on {repo}#{number} "
            "(conversation comments do not support threaded replies)"
        )

    if review_id is None:
        if not pending:
            die(
                f"no pending review on {repo}#{number}; run `gh-review start {repo} {number}` first"
            )
        if len(pending) > 1:
            die(f"multiple pending reviews on {repo}#{number}; pass --review-id")
        review_id = pending[0]

    mutation_input = {
        "pullRequestReviewId": review_id,
        "pullRequestReviewThreadId": thread_id,
        "body": body,
    }
    try:
        data = gh_graphql_mutation(_REPLY_MUTATION, {"input": mutation_input})
    except GhError as exc:
        die(str(exc))

    comment = data["data"]["addPullRequestReviewThreadReply"]["comment"]
    review = comment.get("pullRequestReview") or {}
    click.echo(f"id: {comment['databaseId']}")
    click.echo(f"url: {comment['url']}")
    click.echo(f"review: {review.get('id', review_id)}")
    click.echo(f"state: {review.get('state', 'PENDING')}")
