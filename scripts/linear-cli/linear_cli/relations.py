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

_RELATION_TYPES = ["blocks", "blocked-by", "related", "duplicate", "similar"]

# Linear's IssueRelationType enum has no "blockedBy": blocking is stored once, directionally, and
# "blocked by" is the same row read from the other issue. So the CLI keeps the term and resolves it
# by swapping the two issues.
_INVERSE_DISPLAY: dict[str, str] = {"blocks": "blocked-by"}


def _resolve(issue_id: str, type: str, related_id: str) -> tuple[str, str, str]:
    """Map a CLI relation type onto the API's directional form.

    Returns the issue that owns the relation, the API type, and the other issue.
    """
    if type.lower() == "blocked-by":
        return related_id, "blocks", issue_id
    return issue_id, type.lower(), related_id


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

    direct = [
        (Relation.from_graphql(n), False) for n in (issue.get("relations") or {}).get("nodes", [])
    ]
    inverse = [
        (Relation.from_graphql(n, inverse=True), True)
        for n in (issue.get("inverseRelations") or {}).get("nodes", [])
    ]

    if not direct and not inverse:
        click.echo("no relations")
        return

    for rel, is_inverse in direct + inverse:
        rel_type = rel.type or "unknown"
        if is_inverse:
            rel_type = _INVERSE_DISPLAY.get(rel_type, rel_type)
        click.echo(f"{rel_type}  {rel.related_identifier}  ({rel.related_title})")


@cli.command("add")
@click.argument("issue_id")
@click.argument("type", type=click.Choice(_RELATION_TYPES, case_sensitive=False))
@click.argument("related_id")
def add_relation(issue_id: str, type: str, related_id: str) -> None:
    """Add a relation between two issues."""
    source_id, api_type, target_id = _resolve(issue_id, type, related_id)
    try:
        data = execute(
            ISSUE_RELATION_CREATE_MUTATION,
            {"input": {"issueId": source_id, "relatedIssueId": target_id, "type": api_type}},
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
@click.argument("type", type=click.Choice(_RELATION_TYPES, case_sensitive=False))
@click.argument("related_id")
def remove_relation(issue_id: str, type: str, related_id: str) -> None:
    """Remove a relation between two issues."""
    source_id, api_type, target_id = _resolve(issue_id, type, related_id)
    try:
        data = execute(ISSUE_RELATIONS_QUERY, {"id": source_id})
    except LinearError as exc:
        die(str(exc))

    issue = data.get("issue")
    if not issue:
        die(f"issue '{source_id}' not found")

    nodes = (issue.get("relations") or {}).get("nodes", [])
    relation_id: str | None = None
    for node in nodes:
        rel = Relation.from_graphql(node)
        if rel.type == api_type and (rel.related_identifier or "").upper() == target_id.upper():
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
