"""Edit a PR review comment body and/or position."""

from __future__ import annotations

import json
import sys
import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql, gh_graphql_mutation, gh_rest

_ADD_THREAD_MUTATION = textwrap.dedent("""\
    mutation($input: AddPullRequestReviewThreadInput!) {
      addPullRequestReviewThread(input: $input) {
        thread {
          id path isOutdated line startLine diffSide
          comments(first: 1) { nodes { databaseId } }
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
        }
      }
    }""")


@click.command()
@click.argument("repo")
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
    repo: str,
    comment_id: str,
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str | None,
) -> None:
    """Edit a review comment body or reposition it in the diff."""
    positioning = any(x is not None for x in [file_path, line, start_line, side, start_side])

    if body is None and not positioning:
        die("at least one option required")

    is_db_id = comment_id.isdigit()

    if not positioning:
        if is_db_id:
            _body_only_edit_rest(repo, int(comment_id), body)  # type: ignore[arg-type]
        else:
            _body_only_edit_graphql(comment_id, body)  # type: ignore[arg-type]
    else:
        if review_id is None:
            die("--review-id required when changing position")
        if not review_id.startswith("PRR_"):
            die(f"invalid review id: {review_id} (expected PRR_... node id)")
        if is_db_id:
            _reposition_rest(
                repo,
                int(comment_id),
                body,
                file_path,
                line,
                start_line,
                side,
                start_side,
                review_id,
            )
        else:
            _reposition_graphql(
                comment_id,
                body,
                file_path,
                line,
                start_line,
                side,
                start_side,
                review_id,
            )


# -- body-only paths ----------------------------------------------------------


def _body_only_edit_rest(repo: str, comment_id: int, body: str) -> None:
    """PATCH the comment body via REST."""
    try:
        gh_rest("PATCH", f"repos/{repo}/pulls/comments/{comment_id}", body={"body": body})
        click.echo(f"edited: {comment_id} (body updated)")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))


def _body_only_edit_graphql(comment_id: str, body: str) -> None:
    """Update comment body via GraphQL (works for pending comments)."""
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


# -- reposition paths ----------------------------------------------------------


def _merge_fields(
    current: dict[str, Any],
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
) -> dict[str, Any]:
    """Merge CLI args over current comment values."""
    return {
        "body": body if body is not None else current["body"],
        "path": file_path if file_path is not None else current["path"],
        "line": line if line is not None else current.get("line"),
        "side": side if side is not None else current.get("side"),
        "start_line": start_line if start_line is not None else current.get("start_line"),
        "start_side": start_side if start_side is not None else current.get("start_side"),
    }


def _create_replacement(old_id: str | int, review_id: str, merged: dict[str, Any]) -> None:
    """Create a new comment thread from merged fields."""
    mutation_input: dict[str, Any] = {
        "pullRequestReviewId": review_id,
        "path": merged["path"],
        "line": merged["line"],
        "side": merged["side"],
        "body": merged["body"],
        "subjectType": "LINE",
    }
    if merged["start_line"] is not None:
        mutation_input["startLine"] = merged["start_line"]
        mutation_input["startSide"] = merged["start_side"] or merged["side"]

    try:
        data = gh_graphql_mutation(_ADD_THREAD_MUTATION, {"input": mutation_input})
        thread = data["data"]["addPullRequestReviewThread"]["thread"]
        comments = thread.get("comments", {}).get("nodes", [])
        new_id = comments[0]["databaseId"] if comments else thread["id"]
        click.echo(f"edited: {old_id} -> {new_id} (repositioned)")
    except GhError as exc:
        click.echo(f"error: {exc}", err=True)
        click.echo(
            f"warning: comment {old_id} was deleted but could not be recreated",
            err=True,
        )
        sys.exit(1)


def _reposition_rest(
    repo: str,
    comment_id: int,
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str,
) -> None:
    """Delete + recreate via REST (for submitted comments with database IDs)."""
    try:
        raw = gh_rest("GET", f"repos/{repo}/pulls/comments/{comment_id}")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))

    current = json.loads(raw)
    merged = _merge_fields(current, body, file_path, line, start_line, side, start_side)

    try:
        gh_rest("DELETE", f"repos/{repo}/pulls/comments/{comment_id}")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))

    _create_replacement(comment_id, review_id, merged)


def _reposition_graphql(
    comment_id: str,
    body: str | None,
    file_path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str,
) -> None:
    """Delete + recreate via GraphQL (for pending comments with node IDs)."""
    try:
        data = gh_graphql(_QUERY_COMMENT, id=comment_id)
        node = data.get("data", {}).get("node")
        if not node:
            die(f"comment {comment_id} not found")
    except GhError as exc:
        die(str(exc))

    # GraphQL comment has body and path but not line/side (those live on the thread).
    current: dict[str, Any] = {
        "body": node["body"],
        "path": node["path"],
        "line": None,
        "side": None,
        "start_line": None,
        "start_side": None,
    }
    merged = _merge_fields(current, body, file_path, line, start_line, side, start_side)

    if merged["line"] is None:
        die("--line required when repositioning with a node ID")
    if merged["side"] is None:
        merged["side"] = "RIGHT"

    try:
        gh_graphql_mutation(
            _DELETE_COMMENT_MUTATION,
            {"input": {"id": comment_id}},
        )
    except GhError as exc:
        die(str(exc))

    _create_replacement(comment_id, review_id, merged)
