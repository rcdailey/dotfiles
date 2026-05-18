"""Edit a PR review comment body and/or position."""

from __future__ import annotations

import json
import sys
import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation, gh_rest

_ADD_THREAD_MUTATION = textwrap.dedent("""\
    mutation($input: AddPullRequestReviewThreadInput!) {
      addPullRequestReviewThread(input: $input) {
        thread { id path isOutdated line startLine diffSide }
      }
    }""")


@click.command()
@click.argument("repo")
@click.argument("comment_id", type=int)
@click.option("--body", default=None, help="new comment body")
@click.option("--path", default=None, help="file path in the PR")
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
    comment_id: int,
    body: str | None,
    path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str | None,
) -> None:
    """Edit a review comment body or reposition it in the diff."""
    positioning = any(x is not None for x in [path, line, start_line, side, start_side])

    if body is None and not positioning:
        die("at least one option required")

    if not positioning:
        _body_only_edit(repo, comment_id, body)  # type: ignore[arg-type]
    else:
        if review_id is None:
            die("--review-id required when changing position")
        if not review_id.startswith("PRR_"):
            die(f"invalid review id: {review_id} (expected PRR_... node id)")
        _reposition_edit(
            repo, comment_id, body, path, line, start_line, side, start_side, review_id
        )


def _body_only_edit(repo: str, comment_id: int, body: str) -> None:
    """PATCH the comment body in place."""
    try:
        gh_rest("PATCH", f"repos/{repo}/pulls/comments/{comment_id}", body={"body": body})
        click.echo(f"edited: {comment_id} (body updated)")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))


def _reposition_edit(
    repo: str,
    comment_id: int,
    body: str | None,
    path: str | None,
    line: int | None,
    start_line: int | None,
    side: str | None,
    start_side: str | None,
    review_id: str,
) -> None:
    """Delete the old comment and recreate it with merged fields at new position."""
    # Fetch current comment to fill in any omitted fields.
    try:
        raw = gh_rest("GET", f"repos/{repo}/pulls/comments/{comment_id}")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))

    current = json.loads(raw)

    merged_body = body if body is not None else current["body"]
    merged_path = path if path is not None else current["path"]
    merged_line = line if line is not None else current["line"]
    merged_side = side if side is not None else current["side"]
    merged_start_line: int | None = (
        start_line if start_line is not None else current.get("start_line")
    )
    merged_start_side: str | None = (
        start_side if start_side is not None else current.get("start_side")
    )

    # Delete the original comment before creating the replacement.
    try:
        gh_rest("DELETE", f"repos/{repo}/pulls/comments/{comment_id}")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))

    # Recreate at new position via GraphQL.
    mutation_input: dict[str, Any] = {
        "pullRequestReviewId": review_id,
        "path": merged_path,
        "line": merged_line,
        "side": merged_side,
        "body": merged_body,
        "subjectType": "LINE",
    }
    if merged_start_line is not None:
        mutation_input["startLine"] = merged_start_line
        mutation_input["startSide"] = merged_start_side or merged_side

    try:
        data = gh_graphql_mutation(_ADD_THREAD_MUTATION, {"input": mutation_input})
        thread = data["data"]["addPullRequestReviewThread"]["thread"]
        click.echo(f"edited: {comment_id} -> {thread['id']} (repositioned)")
    except GhError as exc:
        click.echo(f"error: {exc}", err=True)
        click.echo(
            f"warning: comment {comment_id} was deleted but could not be recreated",
            err=True,
        )
        sys.exit(1)
