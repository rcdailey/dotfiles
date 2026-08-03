"""Delete a pending or published review comment."""

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
@click.argument("target")
@click.argument("published_id", type=int, required=False)
def cli(target: str, published_id: int | None) -> None:
    """Delete a pending comment or a published comment.

    TARGET is a PRRC_ node ID for pending comments. For published comments,
    TARGET is OWNER/REPO and PUBLISHED_ID is the numeric comment ID.
    """
    if published_id is not None:
        _published_remove(target, published_id)
        return

    try:
        data = gh_graphql_mutation(
            _DELETE_COMMENT_MUTATION,
            {"input": {"id": target}},
        )
        db_id = data["data"]["deletePullRequestReviewComment"]["pullRequestReviewComment"][
            "databaseId"
        ]
        click.echo(f"removed: {db_id}")
    except GhError as exc:
        die(str(exc))


def _published_remove(repo: str, comment_id: int) -> None:
    """Delete a published review comment via REST."""
    try:
        gh_rest("DELETE", f"repos/{repo}/pulls/comments/{comment_id}")
    except GhError as exc:
        die(str(exc))

    click.echo(f"removed: {comment_id}")
