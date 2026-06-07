"""Edit a pending review comment body and/or position."""

from __future__ import annotations

import sys
import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql, gh_graphql_mutation

_ADD_THREAD_MUTATION = textwrap.dedent("""\
    mutation($input: AddPullRequestReviewThreadInput!) {
      addPullRequestReviewThread(input: $input) {
        thread {
          id path isOutdated line startLine diffSide
          comments(first: 1) { nodes { databaseId id } }
        }
      }
    }""")

_UPDATE_COMMENT_MUTATION = textwrap.dedent("""\
    mutation($input: UpdatePullRequestReviewCommentInput!) {
      updatePullRequestReviewComment(input: $input) {
        pullRequestReviewComment { databaseId body }
      }
    }""")

_DELETE_COMMENT_MUTATION = textwrap.dedent("""\
    mutation($input: DeletePullRequestReviewCommentInput!) {
      deletePullRequestReviewComment(input: $input) {
        pullRequestReviewComment { databaseId }
      }
    }""")

_QUERY_COMMENT = textwrap.dedent("""\
    query($id: ID!) {
      node(id: $id) {
        ... on PullRequestReviewComment {
          body
          path
          pullRequestReview { state }
        }
      }
    }""")


@click.command()
@click.argument("comment_id")
@click.option("--body", default=None, help="new comment body")
@click.option("--path", "file_path", default=None, help="file path in the PR")
@click.option("--line", type=int, default=None, help="end line number")
@click.option("--start-line", type=int, default=None, help="start line for multi-line comments")
@click.option(
    "--side",
    type=click.Choice(["LEFT", "RIGHT"]),
    default=None,
    help="diff side",
)
@click.option(
    "--start-side",
    type=click.Choice(["LEFT", "RIGHT"]),
    default=None,
    help="diff side for start line",
)
@click.option("--review-id", default=None, help="PRR_... node id (required when repositioning)")
def cli(
    comment_id: str,
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str | None,
) -> None:
    """Edit a pending review comment body or reposition it in the diff."""
    positioning = any(x is not None for x in [file_path, line, start_line, side, start_side])

    if body is None and not positioning:
        die("at least one option required")

    if not positioning:
        _body_only_edit(comment_id, body)  # type: ignore[arg-type]
    else:
        if review_id is None:
            die("--review-id required when changing position")
        if not review_id.startswith("PRR_"):
            die(f"invalid review id: {review_id} (expected PRR_... node id)")
        _reposition_edit(comment_id, body, file_path, line, start_line, side, start_side, review_id)


def _assert_pending(comment_id: str) -> dict[str, Any]:
    """Query comment and verify its review is PENDING. Returns the node dict."""
    try:
        data = gh_graphql(_QUERY_COMMENT, id=comment_id)
        node = data.get("data", {}).get("node")
        if not node:
            die(f"comment {comment_id} not found")
    except GhError as exc:
        die(str(exc))
    state = node.get("pullRequestReview", {}).get("state", "")
    if state != "PENDING":
        die(f"comment belongs to a {state} review; edit is only for PENDING reviews")
    return node


def _body_only_edit(comment_id: str, body: str) -> None:
    """Update comment body via GraphQL."""
    _assert_pending(comment_id)
    try:
        data = gh_graphql_mutation(
            _UPDATE_COMMENT_MUTATION,
            {"input": {"pullRequestReviewCommentId": comment_id, "body": body}},
        )
        db_id = data["data"]["updatePullRequestReviewComment"]["pullRequestReviewComment"][
            "databaseId"
        ]
        click.echo(f"edited: {db_id} (body updated)")
    except GhError as exc:
        die(str(exc))


def _reposition_edit(
    comment_id: str,
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str,
) -> None:
    """Delete + recreate at new position via GraphQL."""
    node = _assert_pending(comment_id)

    # GraphQL comment has body and path but not line/side (those live on the thread).
    merged_body = body if body is not None else node["body"]
    merged_path = file_path if file_path is not None else node["path"]
    merged_side = side if side is not None else "RIGHT"

    if line is None:
        die("--line required when repositioning")

    # Delete the original comment.
    try:
        gh_graphql_mutation(
            _DELETE_COMMENT_MUTATION,
            {"input": {"id": comment_id}},
        )
    except GhError as exc:
        die(str(exc))

    # Recreate at new position.
    mutation_input: dict[str, Any] = {
        "pullRequestReviewId": review_id,
        "path": merged_path,
        "line": line,
        "side": merged_side,
        "body": merged_body,
        "subjectType": "LINE",
    }
    if start_line is not None:
        mutation_input["startLine"] = start_line
        mutation_input["startSide"] = start_side or merged_side

    try:
        data = gh_graphql_mutation(_ADD_THREAD_MUTATION, {"input": mutation_input})
        thread = data["data"]["addPullRequestReviewThread"]["thread"]
        comments = thread.get("comments", {}).get("nodes", [])
        if comments:
            new_comment = comments[0]
            click.echo(f"comment-id: {new_comment['databaseId']}")
            click.echo(f"comment-node-id: {new_comment['id']}")
        click.echo(f"path: {thread['path']}")
        start = thread.get("startLine")
        end = thread["line"]
        line_str = f"L{start}-{end}" if start and start != end else f"L{end}"
        click.echo(f"line: {line_str}")
    except GhError as exc:
        click.echo(f"error: {exc}", err=True)
        click.echo(
            f"warning: comment {comment_id} was deleted but could not be recreated",
            err=True,
        )
        sys.exit(1)
