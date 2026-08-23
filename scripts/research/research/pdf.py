"""PDF download and OCR subcommand."""

from __future__ import annotations

import subprocess
import sys

import click

from research._budget import budget_cache_hit, budget_refund, budget_reserve
from research._cache import cache_url, get_cache, read_cached_content, write_cached_content
from research._render import DEFAULT_MAX_CHARS, apply_find, truncate_output
from research._source_ledger import record_source


@click.command()
@click.argument("url")
@click.option("--find", help="show only paragraphs matching this pattern")
@click.option("-C", "--context", type=int, default=0, help="paragraphs of context around matches")
@click.option("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
@click.option("--offset", type=int, default=0, help="char offset into content for pagination")
@click.option("--critical", is_flag=True, help="use a reserved post-warning call")
def cli(
    url: str,
    find: str | None,
    context: int,
    max_chars: int,
    offset: int,
    critical: bool,
) -> None:
    """Download, OCR, and convert PDF to markdown."""
    _do_pdf(url, find, context, max_chars, offset, critical)


def _do_pdf(
    url: str,
    find: str | None,
    context: int,
    max_chars: int,
    offset: int = 0,
    critical: bool = False,
) -> None:
    """Internal PDF handler shared with web reroute."""
    base_url = cache_url(url)
    cache = get_cache()

    cached = read_cached_content(base_url)
    if cached is not None:
        budget_cache_hit(cache, base_url)
        text = cached
    else:
        budget_reserve(cache, base_url, critical=critical)
        try:
            result = subprocess.run(
                ["pdf2md", url],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            budget_refund(cache, base_url)
            click.echo("error: command not found: pdf2md", err=True)
            sys.exit(2)

        if result.returncode != 0:
            budget_refund(cache, base_url)
            err = result.stderr.strip() or f"pdf2md exited {result.returncode}"
            click.echo(f"error: pdf failed: {err}", err=True)
            sys.exit(1)

        text = result.stdout
        if text:
            write_cached_content(base_url, text)

    total_len = len(text)
    if offset > 0:
        text = text[offset:]

    if find:
        output = apply_find(text, find, context)
    else:
        output = text

    if offset > 0:
        output = f"[starting at char offset {offset}; total length {total_len}]\n\n" + output

    record_source(url)
    click.echo(truncate_output(output, max_chars), nl=False)
