"""Add an inline comment to a pending PR review."""

from __future__ import annotations

import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation

_THREAD_MUTATION = textwrap.dedent("""\
    mutation($input: AddPullRequestReviewThreadInput!) {
      addPullRequestReviewThread(input: $input) {
        thread { id path isOutdated line startLine diffSide subjectType comments(first: 1) { nodes { databaseId id } } }
      }
    }""")


def _build_line_input(
    review_id: str,
    path: str,
    line: int,
    side: str,
    body: str,
    start_line: int | None,
    start_side: str | None,
) -> dict[str, Any]:
    """Build mutation input for a LINE-level comment."""
    mutation_input: dict[str, Any] = {
        "pullRequestReviewId": review_id,
        "path": path,
        "line": line,
        "side": side,
        "body": body,
        "subjectType": "LINE",
    }
    if start_line is not None:
        mutation_input["startLine"] = start_line
        mutation_input["startSide"] = start_side or side
    return mutation_input


def _build_file_input(review_id: str, path: str, body: str) -> dict[str, Any]:
    """Build mutation input for a FILE-level comment (no line targeting)."""
    return {
        "pullRequestReviewId": review_id,
        "path": path,
        "body": body,
        "subjectType": "FILE",
    }


def _emit_thread(thread: dict[str, Any], fallback_note: str | None = None) -> None:
    """Print thread details to stdout."""
    click.echo(f"id: {thread['id']}")
    comments = thread.get("comments", {}).get("nodes", [])
    if comments:
        click.echo(f"comment-id: {comments[0]['databaseId']}")
        click.echo(f"comment-node-id: {comments[0]['id']}")
    click.echo(f"path: {thread['path']}")

    subject_type = thread.get("subjectType", "LINE")
    if subject_type == "FILE":
        click.echo("line: file-level")
    else:
        start = thread.get("startLine")
        end = thread["line"]
        line_str = f"L{start}-{end}" if start and start != end else f"L{end}"
        click.echo(f"line: {line_str}")

    if fallback_note:
        click.echo(f"note: {fallback_note}")
    if thread.get("isOutdated"):
        click.echo("warning: comment targets outdated code (file has changed)")


@click.command()
@click.option("--review-id", required=True, help="PRR_... node id")
@click.option("--path", required=True, help="file path in the PR")
@click.option(
    "--line",
    type=int,
    default=None,
    help="line number (or end line for multi-line); omit for file-level",
)
@click.option("--start-line", type=int, default=None, help="start line for multi-line comments")
@click.option("--body", required=True, help="comment body")
@click.option(
    "--side",
    type=click.Choice(["LEFT", "RIGHT"]),
    default="RIGHT",
    show_default=True,
    help="diff side",
)
@click.option(
    "--start-side",
    type=click.Choice(["LEFT", "RIGHT"]),
    default=None,
    help="diff side for start line",
)
def cli(
    review_id: str,
    path: str,
    line: int | None,
    start_line: int | None,
    body: str,
    side: str,
    start_side: str | None,
) -> None:
    """Add inline comment to pending review.

    Targets a specific line by default. If --line is omitted, posts a
    file-level comment. If the targeted line is outside the diff, automatically
    retries as a file-level comment on the same file.
    """
    if not review_id.startswith("PRR_"):
        die(f"invalid review id: {review_id} (expected PRR_... node id)")

    # Explicit file-level: no line provided.
    if line is None:
        file_input = _build_file_input(review_id, path, body)
        try:
            data = gh_graphql_mutation(_THREAD_MUTATION, {"input": file_input})
        except GhError as exc:
            die(str(exc))
        thread = data["data"]["addPullRequestReviewThread"]["thread"]
        if thread is None:
            die(f"{path} is not in the PR diff")
        _emit_thread(thread)
        return

    # Line-level attempt.
    line_input = _build_line_input(review_id, path, line, side, body, start_line, start_side)
    try:
        data = gh_graphql_mutation(_THREAD_MUTATION, {"input": line_input})
    except GhError as exc:
        die(str(exc))

    thread = data["data"]["addPullRequestReviewThread"]["thread"]
    if thread is not None:
        _emit_thread(thread)
        return

    # Line was outside diff hunks. Retry as file-level.
    line_desc = f"L{start_line}-{line}" if start_line else f"L{line}"
    file_input = _build_file_input(review_id, path, body)
    try:
        data = gh_graphql_mutation(_THREAD_MUTATION, {"input": file_input})
    except GhError as exc:
        die(f"{path} {line_desc} is outside the diff and file-level fallback failed: {exc}")

    thread = data["data"]["addPullRequestReviewThread"]["thread"]
    if thread is None:
        die(f"{path} {line_desc} is outside the diff and {path} is not in the PR diff")
    _emit_thread(
        thread, fallback_note=f"{line_desc} was outside diff; posted as file-level comment"
    )
