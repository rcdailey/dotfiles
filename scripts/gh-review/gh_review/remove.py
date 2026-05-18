"""Delete a pending review comment by node ID."""

from __future__ import annotations

import textwrap

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation

_DELETE_COMMENT_MUTATION = textwrap.dedent("""\
    mutation($input: DeletePullRequestReviewCommentInput!) {
      deletePullRequestReviewComment(input: $input) {
        pullRequestReviewComment { databaseId }
      }
    }""")


@click.command()
@click.argument("comment_id")
def cli(comment_id: str) -> None:
    """Delete a pending review comment by node ID."""
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
