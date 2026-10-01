"""Command-line interface."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import click

from mdwrap._errors import MdwrapError
from mdwrap._format import Dialect, rewrap
from mdwrap._settings import resolve_settings

_BOM = "\ufeff"


def _dialect(path: Path) -> Dialect:
    return Dialect.MDX if path.suffix == ".mdx" else Dialect.MARKDOWN


def _format_text(raw: bytes, origin: Path, width: int | None) -> str | None:
    """Return the reflowed text, or None when no width applies.

    Line endings, a UTF-8 BOM, and the presence of a final newline are preserved.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MdwrapError(f"{origin}: not valid UTF-8: {exc}") from exc
    settings = resolve_settings(origin, width_override=width)
    if settings is None:
        return None
    bom = _BOM if text.startswith(_BOM) else ""
    newline = "\r\n" if "\r\n" in text else "\n"
    body = text.removeprefix(bom).replace("\r\n", "\n")
    out = rewrap(body, width=settings.width, tab_width=settings.tab_width, dialect=_dialect(origin))
    return bom + out.replace("\n", newline)


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".mdwrap")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(tmp, path.stat().st_mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _process_file(path: Path, width: int | None, check: bool) -> bool:
    """Format one file; return whether it was (or, with `check`, would be) changed."""
    real = path.resolve()
    if not real.is_file():
        raise MdwrapError(f"{path}: not a file")
    try:
        raw = real.read_bytes()
    except OSError as exc:
        raise MdwrapError(f"{path}: {exc.strerror}") from exc
    out = _format_text(raw, real, width)
    if out is None:
        click.echo(f"no wrap width for {path}; unchanged", err=True)
        return False
    if out.encode("utf-8") == raw:
        return False
    if check:
        click.echo(f"would rewrap: {path}")
        return True
    try:
        _write_atomic(real, out)
    except OSError as exc:
        raise MdwrapError(f"{path}: {exc.strerror or exc}") from exc
    return True


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__import__("mdwrap").__version__, prog_name="mdwrap")
@click.argument("paths", nargs=-1, required=True)
@click.option("--width", type=click.IntRange(min=1), help="Wrap width; overrides config.")
@click.option("--check", is_flag=True, help="Report files that would change; write nothing.")
@click.option(
    "--stdin-filename",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path stdin stands for: picks the dialect and where the config search starts.",
)
def cli(
    paths: tuple[str, ...], width: int | None, check: bool, stdin_filename: Path | None
) -> None:
    """Reflow Markdown and MDX prose in place to the configured line length.

    Width comes from --width, else markdownlint's line-length line_length, else
    .editorconfig max_line_length, each searched upward from the file. With no width,
    files stay unchanged. Use - as the only path to filter stdin to stdout.
    """
    if "-" in paths:
        if len(paths) > 1:
            raise click.UsageError("- must be the only path")
        origin = stdin_filename or Path("stdin.md")
        raw = sys.stdin.buffer.read()
        try:
            out = _format_text(raw, origin.absolute(), width)
        except MdwrapError as exc:
            click.echo(f"error: {exc}", err=True)
            sys.exit(1)
        if out is None:
            click.echo(f"no wrap width for {origin}; unchanged", err=True)
            out = raw.decode("utf-8")
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.exit(1 if check and out.encode("utf-8") != raw else 0)

    failed = changed = False
    for name in paths:
        try:
            changed |= _process_file(Path(name), width, check)
        except MdwrapError as exc:
            click.echo(f"error: {exc}", err=True)
            failed = True
    sys.exit(1 if failed or (check and changed) else 0)
