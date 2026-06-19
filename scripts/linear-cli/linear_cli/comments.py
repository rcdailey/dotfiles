"""Issue comment commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Comment
from linear_cli._queries import COMMENT_CREATE_MUTATION, COMMENT_UPDATE_MUTATION, COMMENTS_QUERY


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List and add comments on Linear issues."""


@cli.command("list")
@click.argument("issue_id")
def list_comments(issue_id: str) -> None:
    """List comments on an issue."""
    try:
        nodes = paginate(
            COMMENTS_QUERY,
            {"issueId": issue_id, "first": 100},
            ["issue", "comments"],
        )
    except LinearError as exc:
        die(str(exc))

    if not nodes:
        click.echo("no comments")
        return
    for node in nodes:
        comment = Comment.from_graphql(node)
        click.echo(f"[{comment.created_at}] {comment.user_name}: {comment.body}")


@cli.command("add")
@click.argument("issue_id")
@click.option("--body", required=True, help="Comment body (markdown).")
@click.option("--parent", "parent_id", default=None, help="Parent comment UUID for threading.")
def add_comment(issue_id: str, body: str, parent_id: str | None) -> None:
    """Add a comment to an issue."""
    variables: dict = {"issueId": issue_id, "body": body}
    if parent_id:
        variables["parentId"] = parent_id

    try:
        data = execute(COMMENT_CREATE_MUTATION, variables)
    except LinearError as exc:
        die(str(exc))

    result = data.get("commentCreate") or {}
    if not result.get("success"):
        die("comment creation failed")

    comment = result.get("comment") or {}
    click.echo(f"comment created: {comment.get('id')}  at {comment.get('createdAt')}")


@cli.command("edit")
@click.argument("comment_id")
@click.option("--body", required=True, help="New comment body (markdown).")
def edit_comment(comment_id: str, body: str) -> None:
    """Edit an existing comment."""
    try:
        data = execute(COMMENT_UPDATE_MUTATION, {"id": comment_id, "body": body})
    except LinearError as exc:
        die(str(exc))

    result = data.get("commentUpdate") or {}
    if not result.get("success"):
        die("comment update failed")

    comment = result.get("comment") or {}
    click.echo(f"comment updated: {comment.get('id')}  at {comment.get('updatedAt')}")
