"""Reply to a PR review comment thread."""

from __future__ import annotations

import json

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_rest


@click.command()
@click.argument("repo")
@click.argument("number", type=int)
@click.argument("comment_id", type=int)
@click.option("--body", required=True, help="reply body")
def cli(repo: str, number: int, comment_id: int, body: str) -> None:
    """Reply to a review comment thread."""
    # Try review comment reply first (most common case).
    try:
        raw = gh_rest(
            "POST",
            f"repos/{repo}/pulls/{number}/comments/{comment_id}/replies",
            body={"body": body},
            jq="{id, html_url}",
        )
        data = json.loads(raw)
        click.echo(f"id: {data['id']}")
        click.echo(f"url: {data['html_url']}")
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
        click.echo(f"id: {data['id']}")
        click.echo(f"url: {data['html_url']}")
    except GhError as exc:
        die(f"failed to post reply: {exc}")
