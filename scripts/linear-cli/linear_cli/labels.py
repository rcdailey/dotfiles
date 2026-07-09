"""Issue label listing commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute, paginate
from linear_cli._models import Label
from linear_cli._queries import LABEL_CHILDREN_QUERY, LABEL_GROUPS_QUERY, LABELS_QUERY


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Inspect Linear issue labels."""


@cli.command("groups")
def list_groups() -> None:
    """List label group names, one per line."""
    filt: dict = {"isGroup": {"eq": True}}
    try:
        data = execute(LABEL_GROUPS_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("issueLabels") or {}).get("nodes", [])
    if not nodes:
        click.echo("no groups found")
        return

    for node in nodes:
        name = node.get("name", "")
        if name:
            click.echo(name)


@cli.command("list")
@click.option(
    "--group",
    "groups",
    multiple=True,
    help="Expand children of this group (repeatable).",
)
def list_labels(groups: tuple[str, ...]) -> None:
    """List issue labels. Groups shown with (group) suffix; children collapsed by default.

    Use --group NAME to expand children of a specific group.
    """
    if groups:
        _list_with_groups(groups)
    else:
        _list_all()


def _list_all() -> None:
    """Fetch all labels via pagination and partition into groups vs ungrouped."""
    variables: dict = {"filter": None, "first": 250, "after": None}
    try:
        nodes = paginate(LABELS_QUERY, variables, ["issueLabels"])
    except LinearError as exc:
        die(str(exc))

    if not nodes:
        click.echo("no labels found")
        return

    labels = [Label.from_graphql(n) for n in nodes]
    group_labels = [lb for lb in labels if lb.is_group]
    ungrouped = [lb for lb in labels if not lb.is_group and not lb.parent_name]

    for group in group_labels:
        click.echo(f"{group.name} (group)")

    for label in ungrouped:
        click.echo(label.name)


def _list_with_groups(group_names: tuple[str, ...]) -> None:
    """For each named group, fetch children server-side and display indented."""
    for group_name in group_names:
        filt: dict = {"parent": {"name": {"eq": group_name}}}
        try:
            data = execute(LABEL_CHILDREN_QUERY, {"filter": filt})
        except LinearError as exc:
            die(str(exc))

        click.echo(f"{group_name} (group)")
        nodes = (data.get("issueLabels") or {}).get("nodes", [])
        for node in nodes:
            name = node.get("name", "")
            if name:
                click.echo(f"  {name}")
