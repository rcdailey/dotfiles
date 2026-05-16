"""Delete a pending PR review."""

from __future__ import annotations

import textwrap

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation


@click.command()
@click.argument("review_id", metavar="REVIEW_ID")
def cli(review_id: str) -> None:
    """Delete a pending PR review."""
    if not review_id.startswith("PRR_"):
        die(f"invalid review id: {review_id} (expected PRR_... node id)")
    try:
        data = gh_graphql_mutation(
            textwrap.dedent("""\
                mutation($input: DeletePullRequestReviewInput!) {
                  deletePullRequestReview(input: $input) {
                    pullRequestReview { id state }
                  }
                }"""),
            {"input": {"pullRequestReviewId": review_id}},
        )
        review = data["data"]["deletePullRequestReview"]["pullRequestReview"]
        click.echo(f"deleted: {review['id']} (was {review['state']})")
    except GhError as exc:
        die(str(exc))
