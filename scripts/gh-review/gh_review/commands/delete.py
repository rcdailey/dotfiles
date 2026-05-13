"""Delete a pending PR review."""

from __future__ import annotations

import textwrap

from ..gh import die, gh_graphql_mutation


def run(review_id: str) -> None:
    if not review_id.startswith("PRR_"):
        die(f"invalid review id: {review_id} (expected PRR_... node id)")
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
    print(f"deleted: {review['id']} (was {review['state']})")
