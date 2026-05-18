"""Add an inline comment to a pending PR review."""

from __future__ import annotations

import textwrap
from typing import Any

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation


@click.command()
@click.option("--review-id", required=True, help="PRR_... node id")
@click.option("--path", required=True, help="file path in the PR")
@click.option("--line", type=int, required=True, help="line number (or end line for multi-line)")
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
    line: int,
    start_line: int | None,
    body: str,
    side: str,
    start_side: str | None,
) -> None:
    """Add inline comment to pending review."""
    if not review_id.startswith("PRR_"):
        die(f"invalid review id: {review_id} (expected PRR_... node id)")

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

    try:
        data = gh_graphql_mutation(
            textwrap.dedent("""\
                mutation($input: AddPullRequestReviewThreadInput!) {
                  addPullRequestReviewThread(input: $input) {
                    thread { id path isOutdated line startLine diffSide comments(first: 1) { nodes { databaseId id } } }
                  }
                }"""),
            {"input": mutation_input},
        )
        thread = data["data"]["addPullRequestReviewThread"]["thread"]
        if thread is None:
            line_desc = f"L{start_line}-{line}" if start_line else f"L{line}"
            die(
                f"{path} {line_desc} is outside the diff hunks. "
                "GitHub API does not support comments on non-diff lines. "
                "Post this comment manually through the GitHub UI."
            )

        start = thread.get("startLine")
        end = thread["line"]
        line_str = f"L{start}-{end}" if start and start != end else f"L{end}"
        click.echo(f"id: {thread['id']}")
        comments = thread.get("comments", {}).get("nodes", [])
        if comments:
            click.echo(f"comment-id: {comments[0]['databaseId']}")
            click.echo(f"comment-node-id: {comments[0]['id']}")
        click.echo(f"path: {thread['path']}")
        click.echo(f"line: {line_str}")
        if thread.get("isOutdated"):
            click.echo("warning: comment targets outdated code (file has changed)")
    except GhError as exc:
        die(str(exc))
