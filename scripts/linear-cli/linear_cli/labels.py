"""Issue label listing commands."""

from __future__ import annotations

import click

from linear_cli._click import HelpfulGroup
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._models import Label
from linear_cli._queries import LABELS_QUERY
from linear_cli._resolve import resolve_team_id


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Inspect Linear issue labels."""


@cli.command("list")
@click.option("--team", "team_key", default=None, help="Team key (e.g. ENG).")
def list_labels(team_key: str | None) -> None:
    """List issue labels, optionally filtered by team."""
    team_id = resolve_team_id(team_key) if team_key else None
    filt: dict | None = None
    if team_id:
        filt = {"team": {"id": {"eq": team_id}}}
    try:
        data = execute(LABELS_QUERY, {"filter": filt})
    except LinearError as exc:
        die(str(exc))

    nodes = (data.get("issueLabels") or {}).get("nodes", [])
    if not nodes:
        click.echo("no labels found")
        return

    labels = [Label.from_graphql(n) for n in nodes]
    groups = [lb for lb in labels if lb.is_group]
    ungrouped = [lb for lb in labels if not lb.is_group and not lb.parent_name]

    for group in groups:
        click.echo(f"{group.name} (group)")
        for child_name in group.children:
            click.echo(f"  {child_name}")

    for label in ungrouped:
        click.echo(label.name)
