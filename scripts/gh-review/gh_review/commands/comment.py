"""Add an inline comment to a pending PR review."""

from __future__ import annotations

import sys
import textwrap
from typing import Any

from ..gh import die, gh_graphql_mutation


def run(
    review_id: str,
    path: str,
    line: int,
    body: str,
    *,
    side: str = "RIGHT",
    start_line: int | None = None,
    start_side: str | None = None,
) -> None:
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

    data = gh_graphql_mutation(
        textwrap.dedent("""\
            mutation($input: AddPullRequestReviewThreadInput!) {
              addPullRequestReviewThread(input: $input) {
                thread { id path isOutdated line startLine diffSide }
              }
            }"""),
        {"input": mutation_input},
    )
    thread = data["data"]["addPullRequestReviewThread"]["thread"]
    if thread is None:
        line_desc = f"L{start_line}-{line}" if start_line else f"L{line}"
        print(
            f"error: {path} {line_desc} is outside the diff hunks. "
            f"GitHub API does not support comments on non-diff lines. "
            f"Post this comment manually through the GitHub UI.",
            file=sys.stderr,
        )
        sys.exit(1)

    start = thread.get("startLine")
    end = thread["line"]
    line_str = f"L{start}-{end}" if start and start != end else f"L{end}"
    print(f"id: {thread['id']}")
    print(f"path: {thread['path']}")
    print(f"line: {line_str}")
    if thread.get("isOutdated"):
        print("warning: comment targets outdated code (file has changed)")
