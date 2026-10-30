"""Custom Click classes: full help on usage errors and compact recursive help."""

from __future__ import annotations

import click


class HelpfulGroup(click.Group):
    """Click group that appends the failing command's help to usage errors."""

    def invoke(self, ctx: click.Context) -> None:
        try:
            return super().invoke(ctx)
        except click.UsageError as exc:
            if exc.ctx is not None:
                click.echo(exc.format_message(), err=True)
                click.echo("", err=True)
                click.echo(exc.ctx.get_help(), err=True)
            else:
                click.echo(exc.format_message(), err=True)
            raise SystemExit(exc.exit_code) from None


class RecursiveHelpGroup(HelpfulGroup):
    """Click group whose help lists every leaf command in one compact view.

    Each leaf renders as a signature line plus one indented line per documented option, so a
    single ``--help`` call carries the semantics that per-command help would otherwise hold.
    """

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Render every leaf command from Click's command metadata."""
        formatter.write("\n".join(_command_lines(self, ctx, _context_prefix(ctx))))
        formatter.write("\n")


def _context_prefix(ctx: click.Context) -> tuple[str, ...]:
    """Return the current command path without the root executable."""
    names = []
    current = ctx
    while current.parent is not None:
        if current.info_name:
            names.append(current.info_name)
        current = current.parent
    return tuple(reversed(names))


def _command_lines(group: click.Group, ctx: click.Context, prefix: tuple[str, ...]) -> list[str]:
    """Return compact signatures, summaries, and option notes for a command tree."""
    lines = []
    for name in group.list_commands(ctx):
        command = group.get_command(ctx, name)
        if command is None or command.hidden:
            continue
        child_ctx = click.Context(command, info_name=name, parent=ctx)
        path = (*prefix, name)
        if isinstance(command, click.Group):
            lines.extend(_command_lines(command, child_ctx, path))
            continue
        signature = _signature(command, child_ctx, path)
        summary = _summary(command)
        lines.append(f"{signature}  {summary}" if summary else signature)
        lines.extend(_option_notes(command, child_ctx))
    return lines


def _options(command: click.Command, ctx: click.Context) -> list[click.Option]:
    """Return the command's visible options, excluding --help."""
    help_option = command.get_help_option(ctx)
    return [
        param
        for param in command.get_params(ctx)
        if isinstance(param, click.Option) and param is not help_option and not param.hidden
    ]


def _signature(command: click.Command, ctx: click.Context, path: tuple[str, ...]) -> str:
    """Build a compact command signature from Click parameters."""
    parts = [" ".join(path)]
    parts += [
        param.make_metavar(ctx)
        for param in command.get_params(ctx)
        if isinstance(param, click.Argument)
    ]
    for option in _options(command, ctx):
        record = option.get_help_record(ctx)
        if record is None:
            continue
        value = _with_default(record[0].replace(", ", "/").replace(" / ", "/"), option)
        parts.append(value if option.required else f"[{value}]")
    return " ".join(parts)


def _with_default(value: str, option: click.Option) -> str:
    """Append simple non-flag defaults without exposing Click sentinels."""
    default = option.default
    if option.is_flag or isinstance(default, bool):
        return value
    if not isinstance(default, (str, int, float)):
        return value
    return f"{value}={default}"


def _option_notes(command: click.Command, ctx: click.Context) -> list[str]:
    """Return one indented help line per option that has help text."""
    notes = []
    for option in _options(command, ctx):
        text = " ".join((option.help or "").split()).removesuffix(".")
        if text:
            notes.append(f"  {option.opts[0]}: {text}")
    return notes


def _summary(command: click.Command) -> str:
    """Return the first help paragraph on one line."""
    text = command.short_help or command.help or ""
    paragraph = text.strip().split("\n\n", 1)[0]
    return " ".join(paragraph.split()).removesuffix(".")
