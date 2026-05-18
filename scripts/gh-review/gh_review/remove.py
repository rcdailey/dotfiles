"""Delete a single PR review comment by database ID."""

from __future__ import annotations

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_rest


@click.command()
@click.argument("repo")
@click.argument("comment_id", type=int)
def cli(repo: str, comment_id: int) -> None:
    """Delete a single review comment by database ID."""
    try:
        gh_rest("DELETE", f"repos/{repo}/pulls/comments/{comment_id}")
        click.echo(f"removed: {comment_id}")
    except GhError as exc:
        die(str(exc))
