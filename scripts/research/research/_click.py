"""Custom Click classes with compact recursive help."""

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
    """Click group that renders compact help for every leaf command."""

    def format_help(
        self,
        ctx: click.Context,
        formatter: click.HelpFormatter,
    ) -> None:
        """Render every leaf command from Click's command metadata."""
        prefix = _context_prefix(ctx)
        lines = _command_lines(self, ctx, prefix)
        formatter.write("\n".join(lines))
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


def _command_lines(
    group: click.Group,
    ctx: click.Context,
    prefix: tuple[str, ...],
) -> list[str]:
    """Return compact signatures and summaries for a command tree."""
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
    return lines


def _signature(
    command: click.Command,
    ctx: click.Context,
    path: tuple[str, ...],
) -> str:
    """Build a compact command signature from Click parameters."""
    parts = [" ".join(path)]
    help_option = command.get_help_option(ctx)
    for param in command.get_params(ctx):
        if param is help_option:
            continue
        if isinstance(param, click.Argument):
            parts.append(param.make_metavar(ctx))
            continue
        if not isinstance(param, click.Option):
            continue
        record = param.get_help_record(ctx)
        if record is None:
            continue
        value = record[0].replace(", ", "/").replace(" / ", "/")
        value = _with_default(value, param)
        parts.append(value if param.required else f"[{value}]")
    return " ".join(parts)


def _with_default(value: str, option: click.Option) -> str:
    """Append simple non-flag defaults without exposing Click sentinels."""
    default = option.default
    if option.is_flag or isinstance(default, bool):
        return value
    if not isinstance(default, (str, int, float)):
        return value
    return f"{value}={default}"


def _summary(command: click.Command) -> str:
    """Return the first help paragraph on one line."""
    text = command.short_help or command.help or ""
    paragraph = text.strip().split("\n\n", 1)[0]
    return " ".join(paragraph.split()).removesuffix(".")
