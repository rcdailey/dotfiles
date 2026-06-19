"""Issue link (attachment) commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Attachment
from linear_cli._queries import (
    ATTACHMENT_DELETE_MUTATION,
    ATTACHMENT_LINK_URL_MUTATION,
    ATTACHMENTS_QUERY,
)


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List, add, and remove URL links on issues."""


@cli.command("list")
@click.argument("issue_id")
def list_links(issue_id: str) -> None:
    """List URL links on an issue."""
    try:
        data = execute(ATTACHMENTS_QUERY, {"id": issue_id})
    except LinearError as exc:
        die(str(exc))

    issue = data.get("issue")
    if not issue:
        die(f"issue '{issue_id}' not found")

    nodes = (issue.get("attachments") or {}).get("nodes", [])
    if not nodes:
        click.echo("no links")
        return
    for node in nodes:
        att = Attachment.from_graphql(node)
        if att.title:
            click.echo(f"{att.title}: {att.url}")
        else:
            click.echo(att.url)


@cli.command("add")
@click.argument("issue_id")
@click.argument("url")
@click.option("--title", default=None, help="Optional display title for the link.")
def add_link(issue_id: str, url: str, title: str | None) -> None:
    """Add a URL link to an issue."""
    variables: dict = {"issueId": issue_id, "url": url}
    if title:
        variables["title"] = title

    try:
        data = execute(ATTACHMENT_LINK_URL_MUTATION, variables)
    except LinearError as exc:
        die(str(exc))

    result = data.get("attachmentLinkURL") or {}
    if not result.get("success"):
        die("link creation failed")

    att = result.get("attachment") or {}
    label = att.get("title") or att.get("url", url)
    click.echo(f"link added: {label}")


@cli.command("remove")
@click.argument("link_id")
def remove_link(link_id: str) -> None:
    """Remove a link by its ID."""
    try:
        data = execute(ATTACHMENT_DELETE_MUTATION, {"id": link_id})
    except LinearError as exc:
        die(str(exc))

    result = data.get("attachmentDelete") or {}
    if not result.get("success"):
        die("link removal failed")

    click.echo(f"link removed: {link_id}")
