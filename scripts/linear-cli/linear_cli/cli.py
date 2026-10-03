"""Root CLI group."""

from __future__ import annotations

import click

from linear_cli import (
    api,
    auth,
    comments,
    documents,
    issues,
    labels,
    links,
    me,
    milestones,
    project_updates,
    projects,
    relations,
    states,
    teams,
)
from linear_cli._click import HelpfulGroup


@click.group(
    cls=HelpfulGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__import__("linear_cli").__version__, prog_name="linear-cli")
def cli() -> None:
    """LLM-optimized Linear project management CLI."""


cli.add_command(api.cli, "api")
cli.add_command(auth.cli, "auth")
cli.add_command(comments.cli, "comments")
cli.add_command(documents.cli, "documents")
cli.add_command(issues.cli, "issues")
cli.add_command(labels.cli, "labels")
cli.add_command(links.cli, "links")
cli.add_command(me.cli, "me")
cli.add_command(milestones.cli, "milestones")
cli.add_command(project_updates.cli, "project-updates")
cli.add_command(projects.cli, "projects")
cli.add_command(relations.cli, "relations")
cli.add_command(states.cli, "states")
cli.add_command(teams.cli, "teams")
