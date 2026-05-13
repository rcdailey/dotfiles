"""Start a pending PR review."""

from __future__ import annotations

import textwrap

from ..gh import die, gh_graphql, gh_graphql_mutation, split_repo


def _get_pr_identifiers(repo: str, number: int) -> tuple[str, str]:
    """Return (node_id, head_oid) for a pull request."""
    owner, name = split_repo(repo)
    data = gh_graphql(
        textwrap.dedent("""\
            query($owner:String!,$repo:String!,$number:Int!) {
              repository(owner:$owner,name:$repo) {
                pullRequest(number:$number) { id headRefOid }
              }
            }"""),
        owner=owner,
        repo=name,
        number=str(number),
    )
    pr = data["data"]["repository"]["pullRequest"]
    if not pr:
        die(f"PR #{number} not found in {repo}")
    return pr["id"], pr["headRefOid"]


def run(repo: str, number: int) -> None:
    pr_id, head_oid = _get_pr_identifiers(repo, number)
    data = gh_graphql_mutation(
        textwrap.dedent("""\
            mutation($input: AddPullRequestReviewInput!) {
              addPullRequestReview(input: $input) {
                pullRequestReview { id state }
              }
            }"""),
        {"input": {"pullRequestId": pr_id, "commitOID": head_oid}},
    )
    review = data["data"]["addPullRequestReview"]["pullRequestReview"]
    print(f"id: {review['id']}")
    print(f"state: {review['state']}")
