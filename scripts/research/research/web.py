"""Web search and fetch subcommand."""

from __future__ import annotations

import sys

import click

from research._budget import budget_reserve
from research._cache import get_cache, read_cached_content, write_cached_content
from research._linkup import (
    SearchError,
    fetch_markdown,
    format_search_results,
    get_client,
)
from research._render import (
    apply_find,
    is_github_url,
    is_pdf_url,
    reroute_message,
    strip_github_host,
    truncate_output,
)

DEFAULT_MAX_RESULTS = 5
DEFAULT_MAX_CHARS = 20000


@click.group(invoke_without_command=False)
def cli():
    """Web search and page fetching via Linkup."""


@cli.command(name="search")
@click.argument("query")
@click.option("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
def search_cmd(query: str, max_results: int) -> None:
    """Search the web via Linkup."""
    cache = get_cache()
    budget_reserve(cache, None)

    try:
        from research._linkup import search

        results = search(query, max_results)
        click.echo(format_search_results(results))
    except SearchError as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)


@cli.command(name="fetch")
@click.argument("url")
@click.option("--find", help="show only paragraphs matching this pattern")
@click.option("-C", "--context", type=int, default=0, help="paragraphs of context around matches")
@click.option("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
def fetch_cmd(url: str, find: str | None, context: int, max_chars: int) -> None:
    """Fetch a URL as clean markdown."""
    # Check for reroutes before burning budget
    if is_github_url(url):
        path = strip_github_host(url)
        parts = path.split("/")
        # Only reroute when URL maps to a clear owner/repo pair.
        # Skip orgs/ paths (org-level discussions, profiles) since scout
        # cannot access those; let them fall through to web fetch.
        if len(parts) >= 2 and parts[0] != "orgs":
            owner, repo = parts[0], parts[1]

            # Detect owner/repo/discussions/N and reroute to scout discussion
            if len(parts) >= 4 and parts[2] == "discussions" and parts[3].isdigit():
                number = int(parts[3])
                reroute_message(
                    url,
                    f"scout discussion {owner}/{repo} {number}",
                    "github.com discussion",
                )
                from research._ghapi import APIError, view_discussion
                from research._render import format_issue_body
                from research.scout.issues import _render_comments

                try:
                    data = view_discussion(owner, repo, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                category = data.get("category", {}).get("name", "")
                cat_str = f" [{category}]" if category else ""
                click.echo(
                    format_issue_body(
                        data["number"],
                        data.get("title", "N/A") + cat_str,
                        "open",
                        data.get("createdAt", ""),
                        data.get("body", ""),
                    )
                )
                _render_comments(data.get("comments", []))
                return

            reroute_message(url, f"scout orient {owner}/{repo}", "github.com pages")
            from research.scout.explore import _render_orient

            _render_orient(owner, repo, ref=None, brief=False)
            return

    if is_pdf_url(url):
        reroute_message(url, f"pdf {url}", "URL points to a PDF")
        from research.pdf import _do_pdf

        _do_pdf(url, find, context, max_chars)
        return

    base_url = url.split("?")[0]
    cache = get_cache()

    cached = read_cached_content(base_url)
    if cached is not None:
        markdown = cached
    else:
        budget_reserve(cache, base_url)
        client = get_client()
        try:
            markdown = fetch_markdown(client, url)
        except Exception as e:
            # Check for file URL error
            if type(e).__name__ == "LinkupFetchUrlIsFileError":
                reroute_message(url, f"pdf {url}", "backend reported URL serves a file")
                from research.pdf import _do_pdf

                _do_pdf(url, find, context, max_chars)
                return
            from research._linkup import translate_error

            click.echo(translate_error("fetch", e), err=True)
            sys.exit(1)
        write_cached_content(base_url, markdown)

    if find:
        output = apply_find(markdown, find, context)
    else:
        output = markdown
    click.echo(truncate_output(output, max_chars))
