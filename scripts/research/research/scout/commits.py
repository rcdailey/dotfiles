"""Commit listing, detail, and file history."""

from __future__ import annotations

import click

from research._budget import budget_reserve
from research._cache import get_cache
from research._ghapi import APIError, file_history, list_commits, view_commit
from research._render import (
    fenced_code,
    format_commit_item,
    kv_line,
    section_heading,
)
from research.scout import cli
from research.scout._common import die, parse_repo


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0]


def _commit_date(c: dict) -> str:
    return c.get("commit", {}).get("committer", {}).get("date", "")[:10] or "N/A"


@cli.command()
@click.argument("repo")
@click.option("--since", help="ISO 8601 date")
@click.option("--until", help="ISO 8601 date")
@click.option("--path", help="filter by path")
@click.option("--author", help="filter by author")
@click.option("--limit", "-L", type=int, default=30)
def commits(
    repo: str,
    since: str | None,
    until: str | None,
    path: str | None,
    author: str | None,
    limit: int,
) -> None:
    """List commits."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)
    try:
        commits_list = list_commits(owner, name, since, until, path, author, limit)
    except APIError as e:
        die(str(e))
    if not commits_list:
        click.echo("No commits found")
        return
    for c in commits_list:
        click.echo(
            format_commit_item(
                c.get("sha", "N/A"),
                _commit_date(c),
                _first_line(c.get("commit", {}).get("message", "")),
            )
        )


@cli.command()
@click.argument("repo")
@click.argument("sha")
def commit(repo: str, sha: str) -> None:
    """View a specific commit with diff."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)
    try:
        data = view_commit(owner, name, sha)
    except APIError as e:
        die(str(e))

    commit_obj = data.get("commit", {})
    committer = commit_obj.get("committer", {})
    author = commit_obj.get("author", {})

    click.echo(f"## Commit {sha[:8]}\n")
    click.echo(kv_line("Date", committer.get("date", "N/A")[:10]))
    click.echo(kv_line("Author", author.get("name", "N/A")))
    click.echo("")
    if commit_obj.get("message"):
        click.echo(commit_obj["message"])
        click.echo("")

    stats = data.get("stats", {})
    if stats:
        click.echo(
            f"**Changes:** +{stats.get('additions', 0)} -{stats.get('deletions', 0)} "
            f"({stats.get('total', 0)} total)"
        )

    files = data.get("files", [])
    if files:
        click.echo(section_heading("Files changed"))
        for f in files:
            click.echo(f"\n**{f.get('filename', 'unknown')}** ({f.get('status', 'modified')})")
            if f.get("patch"):
                click.echo(fenced_code(f["patch"], "diff"))


@cli.command()
@click.argument("repo")
@click.argument("path")
@click.option("--limit", "-L", type=int, default=30)
def history(repo: str, path: str, limit: int) -> None:
    """Commit history for a file."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)
    try:
        commits_list = file_history(owner, name, path, limit)
    except APIError as e:
        die(str(e))
    if not commits_list:
        click.echo(f"No history found for {path}")
        return
    click.echo(f"## History for {path}\n")
    for c in commits_list:
        click.echo(
            format_commit_item(
                c.get("sha", "N/A"),
                _commit_date(c),
                _first_line(c.get("commit", {}).get("message", "")),
            )
        )
