"""Synthesis commands: activity digest, changelog."""

from __future__ import annotations

import datetime
import urllib.error
import urllib.request

import click

from research._budget import budget_reserve
from research._cache import get_cache
from research._ghapi import APIError, list_commits, list_issues, list_prs, list_releases
from research._render import format_commit_item, format_list_item, sub_heading, truncate_output
from research.scout import cli
from research.scout._common import parse_repo


@cli.command()
@click.argument("repo")
@click.option("--days", type=int, default=7)
def activity(repo: str, days: int) -> None:
    """Recent commits, merged PRs, and closed issues synthesized."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    since = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        commits_list = list_commits(owner, name, since=since, limit=50)
    except APIError:
        commits_list = []
    try:
        prs = [
            p
            for p in list_prs(owner, name, state="merged", limit=30)
            if p.get("mergedAt") and p["mergedAt"] >= since
        ]
    except APIError:
        prs = []
    try:
        issues = [
            i
            for i in list_issues(owner, name, state="closed", limit=30)
            if i.get("createdAt") and i["createdAt"] >= since
        ]
    except APIError:
        issues = []

    click.echo(f"## Recent Activity: {repo} (last {days} days)\n")

    if commits_list:
        click.echo(sub_heading(f"Commits ({len(commits_list)} recent)"))
        for c in commits_list[:20]:
            commit_obj = c.get("commit", {})
            click.echo(
                format_commit_item(
                    c.get("sha", "N/A")[:8],
                    commit_obj.get("committer", {}).get("date", "")[:10],
                    commit_obj.get("message", "").split("\n")[0],
                )
            )
        if len(commits_list) > 20:
            click.echo(f"\n... and {len(commits_list) - 20} more")
        click.echo("")

    if prs:
        click.echo(sub_heading(f"Merged PRs ({len(prs)} recent)"))
        for p in prs:
            click.echo(
                format_list_item(
                    p["number"], "merged", p.get("mergedAt", ""), p.get("title", "N/A")
                )
            )
        click.echo("")

    if issues:
        click.echo(sub_heading(f"Closed Issues ({len(issues)} recent)"))
        for i in issues:
            click.echo(
                format_list_item(
                    i["number"], i["state"], i.get("createdAt", ""), i.get("title", "N/A")
                )
            )

    if not any([commits_list, prs, issues]):
        click.echo(f"No recent activity found in {repo} (last {days} days)")


@cli.command()
@click.argument("repo")
@click.option("--since", help="version tag to compare from")
def changelog(repo: str, since: str | None) -> None:
    """CHANGELOG file + recent releases synthesized."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    click.echo(f"## Changelog: {repo}\n")

    changelog_files = ["CHANGELOG.md", "CHANGES.md", "HISTORY.md", "CHANGELOG", "CHANGES"]
    content: str | None = None
    source_name = ""

    for fname in changelog_files:
        url = f"https://raw.githubusercontent.com/{owner}/{name}/HEAD/{fname}"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode("utf-8")
                source_name = fname
                break
        except (urllib.error.URLError, TimeoutError):
            continue

    if content:
        click.echo(sub_heading(f"From {source_name}"))
        click.echo(truncate_output(content, 8000))
        click.echo("")

    try:
        releases = list_releases(owner, name, limit=10)
    except APIError:
        releases = []

    if releases:
        click.echo(sub_heading("Recent Releases"))
        for r in releases:
            tag = r.get("tagName", "N/A")
            published = r.get("publishedAt", "")[:10] if r.get("publishedAt") else "N/A"
            flags = []
            if r.get("isDraft"):
                flags.append("draft")
            if r.get("isPrerelease"):
                flags.append("pre-release")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            click.echo(f"- **{tag}** ({published}){flag_str}")
            if r.get("name"):
                click.echo(f"  {r['name']}")

    _ = since
