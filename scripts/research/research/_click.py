"""Custom Click classes that show full help on usage errors."""

from __future__ import annotations

import click


class HelpfulGroup(click.Group):
    """Click group that appends the failing command's help to usage errors.

    When a subcommand raises UsageError (bad option, missing arg, etc.),
    the full help for that specific command is printed so the caller sees
    what options are actually available.
    """

    def invoke(self, ctx: click.Context) -> None:
        try:
            return super().invoke(ctx)
        except click.UsageError as exc:
            # exc.ctx points to the failing command's context when
            # Click sets it during argument parsing.
            if exc.ctx is not None:
                click.echo(exc.format_message(), err=True)
                click.echo("", err=True)
                click.echo(exc.ctx.get_help(), err=True)
            else:
                click.echo(exc.format_message(), err=True)
            raise SystemExit(exc.exit_code) from None
