"""Document commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Document
from linear_cli._queries import DOCUMENT_QUERY, DOCUMENTS_QUERY


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List and view Linear documents."""


@cli.command("list")
@click.option("--project", "project_name", default=None, help="Filter by project name.")
def list_documents(project_name: str | None) -> None:
    """List documents."""
    try:
        data = execute(DOCUMENTS_QUERY)
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("documents") or {}).get("nodes", [])
    if project_name:
        nodes = [
            n
            for n in nodes
            if (n.get("project") or {}).get("name", "").lower() == project_name.lower()
        ]

    if not nodes:
        click.echo("no documents found")
        return
    for node in nodes:
        doc = Document.from_graphql(node)
        proj = f"  [{doc.project_name}]" if doc.project_name else ""
        click.echo(f"{doc.title}{proj}")


@cli.command("view")
@click.argument("doc_id")
def view_document(doc_id: str) -> None:
    """View a document by ID."""
    try:
        data = execute(DOCUMENT_QUERY, {"id": doc_id})
    except LinearError as exc:
        die(str(exc))

    node = data.get("document")
    if not node:
        die(f"document '{doc_id}' not found")

    doc = Document.from_graphql(node)
    click.echo(f"title:    {doc.title}")
    click.echo(f"project:  {doc.project_name or 'none'}")
    click.echo(f"creator:  {doc.creator_name or 'unknown'}")
    click.echo(f"updated:  {doc.updated_at}")
    if doc.content:
        click.echo("")
        click.echo(doc.content)
