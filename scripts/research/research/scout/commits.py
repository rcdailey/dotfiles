"""Commit listing, detail, and file history."""

from __future__ import annotations

import click

from research._ghapi import (
    APIError,
    file_history,
    list_commit_pulls,
    list_commits,
    view_commit,
)
from research._render import (
    DEFAULT_SCOUT_MAX_CHARS,
    fenced_code,
    format_commit_item,
    kv_line,
    section_heading,
    truncate_output,
)
from research.scout import cli
from research.scout._common import (
    die,
    github_url,
    more_results_hint,
    parse_repo,
    take_limited,
)


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
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
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
    try:
        commits_list = list_commits(owner, name, since, until, path, author, limit + 1)
    except APIError as e:
        die(str(e))
    if not commits_list:
        click.echo("No commits found")
        return
    shown, has_more = take_limited(commits_list, limit)
    for c in shown:
        sha = c.get("sha", "N/A")
        click.echo(
            format_commit_item(
                sha,
                _commit_date(c),
                _first_line(c.get("commit", {}).get("message", "")),
                source_url=c.get("html_url") or github_url(owner, name, "commit", sha),
            )
        )
    if has_more:
        click.echo(more_results_hint(limit))


@cli.command()
@click.argument("repo")
@click.argument("sha")
@click.option("--patch", is_flag=True, help="include file patches")
@click.option("--path", help="filter files by path prefix")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def commit(repo: str, sha: str, patch: bool, path: str | None, max_chars: int) -> None:
    """View a commit summary and associated PRs; add --patch for diffs."""
    owner, name = parse_repo(repo)
    try:
        data = view_commit(owner, name, sha)
        resolved_sha = data.get("sha", sha)
        pulls = list_commit_pulls(owner, name, resolved_sha)
    except APIError as e:
        die(str(e))

    commit_obj = data.get("commit", {})
    committer = commit_obj.get("committer", {})
    author = commit_obj.get("author", {})

    lines = [
        f"## Commit {resolved_sha[:8]}\n",
        kv_line("Date", committer.get("date", "N/A")[:10]),
        kv_line("Author", author.get("name", "N/A")),
        kv_line(
            "Source",
            data.get("html_url") or github_url(owner, name, "commit", resolved_sha),
        ),
        "",
    ]
    for pull in pulls:
        number = pull.get("number", "N/A")
        state = "merged" if pull.get("merged_at") else pull.get("state", "unknown")
        url = pull.get("html_url") or github_url(owner, name, "pull", number)
        lines.append(f"- **Associated PR:** #{number} ({state}) {url}")
    if pulls:
        lines.append("")
    if commit_obj.get("message"):
        lines.extend([commit_obj["message"], ""])

    stats = data.get("stats", {})
    if stats:
        lines.append(
            f"**Changes:** +{stats.get('additions', 0)} -{stats.get('deletions', 0)} "
            f"({stats.get('total', 0)} total)"
        )

    files = data.get("files", [])
    if path:
        files = [item for item in files if item.get("filename", "").startswith(path)]
    if files:
        lines.append(section_heading("Files changed"))
        for f in files:
            filename = f.get("filename", "unknown")
            status = f.get("status", "modified")
            additions = f.get("additions", 0)
            deletions = f.get("deletions", 0)
            lines.append(f"\n**{filename}** ({status}, +{additions} -{deletions})")
            if patch and f.get("patch"):
                lines.append(fenced_code(f["patch"], "diff"))
        if not patch:
            lines.append("\nPatches omitted; rerun with --patch and optionally --path PATH.")
    elif path:
        lines.append(f"\nNo changed files matched path: {path}")
    click.echo(
        truncate_output(
            "\n".join(lines),
            max_chars,
            "narrow patches with --path PATH",
        )
    )


@cli.command()
@click.argument("repo")
@click.argument("path")
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
def history(repo: str, path: str, limit: int) -> None:
    """Commit history for a file."""
    owner, name = parse_repo(repo)
    try:
        commits_list = file_history(owner, name, path, limit + 1)
    except APIError as e:
        die(str(e))
    if not commits_list:
        click.echo(f"No history found for {path}")
        return
    click.echo(f"## History for {path}\n")
    shown, has_more = take_limited(commits_list, limit)
    for c in shown:
        sha = c.get("sha", "N/A")
        click.echo(
            format_commit_item(
                sha,
                _commit_date(c),
                _first_line(c.get("commit", {}).get("message", "")),
                source_url=c.get("html_url") or github_url(owner, name, "commit", sha),
            )
        )
    if has_more:
        click.echo(more_results_hint(limit))
