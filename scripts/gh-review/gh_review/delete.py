"""Delete a pending PR review."""

from __future__ import annotations

import textwrap

import click

from gh_review._errors import GhError, die
from gh_review._gh import current_repo, gh_graphql_mutation
from gh_review._review import pending_reviews

_DELETE_MUTATION = textwrap.dedent("""\
    mutation($input: DeletePullRequestReviewInput!) {
      deletePullRequestReview(input: $input) {
        pullRequestReview { id state }
      }
    }""")


def _resolve_pr(target: str, number: int | None) -> str:
    """Return the pending review id for a PR given repo/number arguments."""
    if number is None:
        if "/" in target:
            die(f"missing PR number for {target}")
        if not target.isdigit():
            die(f"invalid target: {target} (expected PRR_... node id, PR number, or owner/repo)")
        repo, number = current_repo(), int(target)
    else:
        repo = target

    try:
        pending = pending_reviews(repo, number)
    except GhError as exc:
        die(str(exc))
    if not pending:
        die(f"no pending review on {repo}#{number}")
    if len(pending) > 1:
        die(f"multiple pending reviews on {repo}#{number}: {' '.join(pending)}")
    return pending[0]


@click.command()
@click.argument("target", metavar="TARGET")
@click.argument("number", type=int, required=False)
def cli(target: str, number: int | None) -> None:
    """Delete a pending PR review.

    TARGET is a PRR_... review node id, or the PR to look it up from: either
    OWNER/REPO with NUMBER, or just the PR number in the current repository.
    """
    review_id = target if target.startswith("PRR_") else _resolve_pr(target, number)
    try:
        data = gh_graphql_mutation(_DELETE_MUTATION, {"input": {"pullRequestReviewId": review_id}})
    except GhError as exc:
        die(str(exc))
    review = data["data"]["deletePullRequestReview"]["pullRequestReview"]
    click.echo(f"deleted: {review['id']} (was {review['state']})")
