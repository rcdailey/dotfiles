"""Root CLI group."""

from __future__ import annotations

import click

from linear_cli import (
    api,
    auth,
    comment,
    document,
    issue,
    label,
    link,
    me,
    milestone,
    project,
    project_update,
    relation,
    state,
    team,
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
cli.add_command(comment.cli, "comment")
cli.add_command(document.cli, "document")
cli.add_command(issue.cli, "issue")
cli.add_command(label.cli, "label")
cli.add_command(link.cli, "link")
cli.add_command(me.cli, "me")
cli.add_command(milestone.cli, "milestone")
cli.add_command(project.cli, "project")
cli.add_command(project_update.cli, "project-update")
cli.add_command(relation.cli, "relation")
cli.add_command(state.cli, "state")
cli.add_command(team.cli, "team")
