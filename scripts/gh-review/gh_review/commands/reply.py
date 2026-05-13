"""Reply to a PR review comment thread."""

from __future__ import annotations

import json

from ..gh import GhError, die, gh_rest


def run(repo: str, number: int, comment_id: int, body: str) -> None:
    # Try review comment reply first (most common case).
    try:
        raw = gh_rest(
            "POST",
            f"repos/{repo}/pulls/{number}/comments/{comment_id}/replies",
            body={"body": body},
            jq="{id, html_url}",
        )
        data = json.loads(raw)
        print(f"id: {data['id']}")
        print(f"url: {data['html_url']}")
        return
    except GhError:
        pass

    # Fall back to issue comment reply (conversation comment).
    try:
        raw = gh_rest(
            "POST",
            f"repos/{repo}/issues/{number}/comments",
            body={"body": body},
            jq="{id, html_url}",
        )
        data = json.loads(raw)
        print(f"id: {data['id']}")
        print(f"url: {data['html_url']}")
    except GhError as exc:
        die(f"failed to post reply: {exc}")
