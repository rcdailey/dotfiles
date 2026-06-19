"""Issue relation commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Relation
from linear_cli._queries import (
    ISSUE_RELATION_CREATE_MUTATION,
    ISSUE_RELATION_DELETE_MUTATION,
    ISSUE_RELATIONS_QUERY,
)

_CLI_TO_API_TYPE: dict[str, str] = {
    "blocks": "blocks",
    "blocked-by": "blockedBy",
    "related": "related",
    "duplicate": "duplicate",
}

_API_TO_CLI_TYPE: dict[str, str] = {v: k for k, v in _CLI_TO_API_TYPE.items()}


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """List, add, and remove issue relations."""


@cli.command("list")
@click.argument("issue_id")
def list_relations(issue_id: str) -> None:
    """List relations on an issue."""
    try:
        data = execute(ISSUE_RELATIONS_QUERY, {"id": issue_id})
    except LinearError as exc:
        die(str(exc))

    issue = data.get("issue")
    if not issue:
        die(f"issue '{issue_id}' not found")

    nodes = (issue.get("relations") or {}).get("nodes", [])
    if not nodes:
        click.echo("no relations")
        return
    for node in nodes:
        rel = Relation.from_graphql(node)
        rel_type = _API_TO_CLI_TYPE.get(rel.type or "", rel.type or "unknown")
        click.echo(f"{rel_type}  {rel.related_identifier}  ({rel.related_title})")


@cli.command("add")
@click.argument("issue_id")
@click.argument(
    "type",
    type=click.Choice(["blocks", "blocked-by", "related", "duplicate"], case_sensitive=False),
)
@click.argument("related_id")
def add_relation(issue_id: str, type: str, related_id: str) -> None:
    """Add a relation between two issues."""
    api_type = _CLI_TO_API_TYPE[type.lower()]
    try:
        data = execute(
            ISSUE_RELATION_CREATE_MUTATION,
            {"input": {"issueId": issue_id, "relatedIssueId": related_id, "type": api_type}},
        )
    except LinearError as exc:
        die(str(exc))

    result = data.get("issueRelationCreate") or {}
    if not result.get("success"):
        die("relation creation failed")

    rel = result.get("issueRelation") or {}
    click.echo(f"relation created: {type}  {rel.get('id')}")


@cli.command("remove")
@click.argument("issue_id")
@click.argument(
    "type",
    type=click.Choice(["blocks", "blocked-by", "related", "duplicate"], case_sensitive=False),
)
@click.argument("related_id")
def remove_relation(issue_id: str, type: str, related_id: str) -> None:
    """Remove a relation between two issues."""
    try:
        data = execute(ISSUE_RELATIONS_QUERY, {"id": issue_id})
    except LinearError as exc:
        die(str(exc))

    issue = data.get("issue")
    if not issue:
        die(f"issue '{issue_id}' not found")

    api_type = _CLI_TO_API_TYPE[type.lower()]
    nodes = (issue.get("relations") or {}).get("nodes", [])
    relation_id: str | None = None
    for node in nodes:
        rel = Relation.from_graphql(node)
        if rel.type == api_type and (rel.related_identifier or "").upper() == related_id.upper():
            relation_id = rel.id
            break

    if not relation_id:
        die(f"relation '{type} {related_id}' not found on issue '{issue_id}'")

    try:
        del_data = execute(ISSUE_RELATION_DELETE_MUTATION, {"id": relation_id})
    except LinearError as exc:
        die(str(exc))

    result = del_data.get("issueRelationDelete") or {}
    if not result.get("success"):
        die("relation removal failed")

    click.echo(f"relation removed: {type}  {related_id}")
