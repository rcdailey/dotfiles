"""PDF download and OCR subcommand."""

from __future__ import annotations

import subprocess
import sys

import click

from research._budget import budget_reserve
from research._cache import get_cache, read_cached_content, write_cached_content
from research._render import apply_find, truncate_output

DEFAULT_MAX_CHARS = 20000


@click.command()
@click.argument("url")
@click.option("--find", help="show only paragraphs matching this pattern")
@click.option("-C", "--context", type=int, default=0, help="paragraphs of context around matches")
@click.option("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
def cli(url: str, find: str | None, context: int, max_chars: int) -> None:
    """Download, OCR, and convert PDF to markdown."""
    _do_pdf(url, find, context, max_chars)


def _do_pdf(url: str, find: str | None, context: int, max_chars: int) -> None:
    """Internal PDF handler shared with web reroute."""
    base_url = url.split("?")[0]
    cache = get_cache()

    cached = read_cached_content(base_url)
    if cached is not None:
        text = cached
    else:
        budget_reserve(cache, base_url)
        try:
            result = subprocess.run(
                ["pdf2md", url],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            click.echo("error: command not found: pdf2md", err=True)
            sys.exit(2)

        if result.returncode != 0:
            err = result.stderr.strip() or f"pdf2md exited {result.returncode}"
            click.echo(f"error: pdf failed: {err}", err=True)
            sys.exit(1)

        text = result.stdout
        if text:
            write_cached_content(base_url, text)

    if find:
        output = apply_find(text, find, context)
    else:
        output = text
    click.echo(truncate_output(output, max_chars))
