"""Resolve or unresolve a published review comment thread."""

from __future__ import annotations

import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql, gh_graphql_mutation, split_repo

_THREADS_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          reviewThreads(first:100) {
            nodes {
              id
              comments(first:100) { nodes { databaseId } }
            }
          }
        }
      }
    }""")

_RESOLVE_MUTATION = textwrap.dedent("""\
    mutation($input:ResolveReviewThreadInput!) {
      resolveReviewThread(input:$input) {
        thread { id isResolved }
      }
    }""")

_UNRESOLVE_MUTATION = textwrap.dedent("""\
    mutation($input:UnresolveReviewThreadInput!) {
      unresolveReviewThread(input:$input) {
        thread { id isResolved }
      }
    }""")


def _find_thread(threads: list[dict[str, Any]], comment_id: int) -> str | None:
    """Return the thread node ID containing a numeric comment ID."""
    for thread in threads:
        comments = (thread.get("comments") or {}).get("nodes", [])
        if any(comment.get("databaseId") == comment_id for comment in comments):
            return thread["id"]
    return None


def _thread_for_comment(repo: str, number: int, comment_id: int) -> str:
    """Find the review thread containing a comment on a pull request."""
    owner, name = split_repo(repo)
    try:
        data = gh_graphql(
            _THREADS_QUERY,
            owner=owner,
            repo=name,
            number=str(number),
        )
    except GhError as exc:
        die(str(exc))

    pr = data["data"]["repository"]["pullRequest"]
    if not pr:
        die(f"PR #{number} not found in {repo}")

    thread_id = _find_thread(pr["reviewThreads"]["nodes"], comment_id)
    if thread_id is None:
        die(f"comment {comment_id} not found in a review thread on {repo}#{number}")
    return thread_id


@click.command()
@click.argument("repo")
@click.argument("number", type=int)
@click.argument("comment_id", type=int)
@click.option("--undo", is_flag=True, help="unresolve the review thread")
def cli(repo: str, number: int, comment_id: int, undo: bool) -> None:
    """Resolve or unresolve the review thread containing a comment."""
    thread_id = _thread_for_comment(repo, number, comment_id)
    mutation = _UNRESOLVE_MUTATION if undo else _RESOLVE_MUTATION
    try:
        data = gh_graphql_mutation(mutation, {"input": {"threadId": thread_id}})
    except GhError as exc:
        die(str(exc))

    operation = "unresolveReviewThread" if undo else "resolveReviewThread"
    thread = data["data"][operation]["thread"]
    state = "RESOLVED" if thread["isResolved"] else "UNRESOLVED"
    click.echo(f"thread-id: {thread['id']}")
    click.echo(f"comment-id: {comment_id}")
    click.echo(f"state: {state}")
