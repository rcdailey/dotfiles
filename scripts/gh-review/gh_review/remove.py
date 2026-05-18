"""Delete a single PR review comment."""

from __future__ import annotations

import textwrap

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation, gh_rest

_DELETE_COMMENT_MUTATION = textwrap.dedent("""\
    mutation($input: DeletePullRequestReviewCommentInput!) {
      deletePullRequestReviewComment(input: $input) {
        pullRequestReviewComment { databaseId }
      }
    }""")


@click.command()
@click.argument("repo")
@click.argument("comment_id")
def cli(repo: str, comment_id: str) -> None:
    """Delete a single review comment (database ID or node ID)."""
    if comment_id.isdigit():
        _remove_rest(repo, int(comment_id))
    else:
        _remove_graphql(comment_id)


def _remove_rest(repo: str, comment_id: int) -> None:
    """Delete via REST API."""
    try:
        gh_rest("DELETE", f"repos/{repo}/pulls/comments/{comment_id}")
        click.echo(f"removed: {comment_id}")
    except GhError as exc:
        if "404" in str(exc):
            die(f"comment {comment_id} not found")
        die(str(exc))


def _remove_graphql(comment_id: str) -> None:
    """Delete via GraphQL (works for pending comments by node ID)."""
    try:
        data = gh_graphql_mutation(
            _DELETE_COMMENT_MUTATION,
            {"input": {"id": comment_id}},
        )
        db_id = data["data"]["deletePullRequestReviewComment"]["pullRequestReviewComment"][
            "databaseId"
        ]
        click.echo(f"removed: {db_id}")
    except GhError as exc:
        die(str(exc))
