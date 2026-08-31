"""Pending review lookup shared by commands that operate on one."""

from __future__ import annotations

import textwrap

from gh_review._errors import die
from gh_review._gh import gh_graphql, split_repo

_PENDING_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          reviews(first:50, states:[PENDING]) { nodes { id } }
        }
      }
    }""")


def pending_reviews(repo: str, number: int) -> list[str]:
    """Return node ids of your unsubmitted reviews on a pull request."""
    owner, name = split_repo(repo)
    data = gh_graphql(_PENDING_QUERY, owner=owner, repo=name, number=str(number))
    pr = data["data"]["repository"]["pullRequest"]
    if not pr:
        die(f"PR #{number} not found in {repo}")
    return [r["id"] for r in pr["reviews"]["nodes"]]
