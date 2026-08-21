"""Synthesis commands: activity digest, changelog."""

from __future__ import annotations

import datetime
import urllib.error
import urllib.request

import click

from research._ghapi import APIError, list_commits, list_issues, list_prs, list_releases
from research._render import format_commit_item, format_list_item, sub_heading, truncate_output
from research.scout import cli
from research.scout._common import (
    date_text,
    filter_release_dates,
    github_url,
    more_results_hint,
    parse_repo,
    take_limited,
)


def _filter_changelog(content: str, since_tag: str | None) -> str:
    """Return content trimmed to start at the heading containing since tag."""
    if not since_tag:
        return content
    since_lower = since_tag.lower()
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#") and since_lower in line.lower():
            return "".join(lines[i:])
    return content  # tag not found; return full content


def _filter_releases_since_tag(releases: list[dict], since_tag: str) -> list[dict]:
    """Return releases published strictly after the since tag's publish date."""
    since_date: str = ""
    for r in releases:
        if r.get("tagName") == since_tag:
            since_date = r.get("publishedAt") or ""
            break
    if not since_date:
        raise ValueError(f"release tag not found: {since_tag}")
    return [r for r in releases if (r.get("publishedAt") or "") > since_date]


@cli.command()
@click.argument("repo")
@click.option("--days", type=int, default=7)
def activity(repo: str, days: int) -> None:
    """Recent commits, merged PRs, and closed issues synthesized."""
    owner, name = parse_repo(repo)

    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    since = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        commits_list = list_commits(owner, name, since=since, limit=51)
    except APIError as error:
        click.echo(f"warning: commits unavailable: {error}", err=True)
        commits_list = []
    try:
        prs = [
            p
            for p in list_prs(owner, name, state="merged", limit=31)
            if p.get("mergedAt") and p["mergedAt"] >= since
        ]
    except APIError as error:
        click.echo(f"warning: PRs unavailable: {error}", err=True)
        prs = []
    try:
        issues = [
            i
            for i in list_issues(owner, name, state="closed", limit=31)
            if i.get("closedAt") and i["closedAt"] >= since
        ]
    except APIError as error:
        click.echo(f"warning: issues unavailable: {error}", err=True)
        issues = []

    click.echo(f"## Recent Activity: {repo} (last {days} days)\n")

    if commits_list:
        shown_commits, commits_more = take_limited(commits_list, 50)
        click.echo(sub_heading(f"Commits ({len(shown_commits)} recent)"))
        for c in shown_commits[:20]:
            sha = c.get("sha", "N/A")
            commit_obj = c.get("commit", {})
            click.echo(
                format_commit_item(
                    sha,
                    commit_obj.get("committer", {}).get("date", "")[:10],
                    commit_obj.get("message", "").split("\n")[0],
                    source_url=c.get("html_url") or github_url(owner, name, "commit", sha),
                )
            )
        if len(shown_commits) > 20:
            click.echo(f"\n... and {len(shown_commits) - 20} more")
        if commits_more:
            click.echo(more_results_hint(50))
        click.echo("")

    if prs:
        shown_prs, prs_more = take_limited(prs, 30)
        click.echo(sub_heading(f"Merged PRs ({len(shown_prs)} recent)"))
        for p in shown_prs:
            click.echo(
                format_list_item(
                    p["number"],
                    "merged",
                    p.get("mergedAt", ""),
                    p.get("title", "N/A"),
                    source_url=p.get("url") or github_url(owner, name, "pull", p["number"]),
                )
            )
        if prs_more:
            click.echo(more_results_hint(30))
        click.echo("")

    if issues:
        shown_issues, issues_more = take_limited(issues, 30)
        click.echo(sub_heading(f"Closed Issues ({len(shown_issues)} recent)"))
        for i in shown_issues:
            click.echo(
                format_list_item(
                    i["number"],
                    i["state"],
                    i.get("closedAt", ""),
                    i.get("title", "N/A"),
                    source_url=i.get("url") or github_url(owner, name, "issues", i["number"]),
                )
            )
        if issues_more:
            click.echo(more_results_hint(30))

    if not any([commits_list, prs, issues]):
        click.echo(f"No recent activity found in {repo} (last {days} days)")


@cli.command()
@click.argument("repo")
@click.option("--since-tag", help="version tag to compare from")
@click.option("--since", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--until", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--limit", type=click.IntRange(min=1), default=10)
def changelog(
    repo: str,
    since_tag: str | None,
    since: datetime.datetime | None,
    until: datetime.datetime | None,
    limit: int,
) -> None:
    """CHANGELOG file + recent releases synthesized."""
    owner, name = parse_repo(repo)

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
        click.echo(f"Source: {url}\n")
        click.echo(
            truncate_output(
                _filter_changelog(content, since_tag),
                8000,
                "use --since-tag or date bounds to narrow the changelog",
            )
        )
        click.echo("")

    since_text = date_text(since)
    until_text = date_text(until)
    if since_text and until_text and since_text > until_text:
        raise click.UsageError("--since must not be after --until")
    fetch_limit = 1000 if since_tag or since_text or until_text else limit + 1
    try:
        releases = list_releases(owner, name, limit=fetch_limit)
    except APIError as error:
        click.echo(f"warning: releases unavailable: {error}", err=True)
        releases = []

    if since_tag:
        try:
            releases = _filter_releases_since_tag(releases, since_tag)
        except ValueError as error:
            raise click.ClickException(str(error)) from error
    releases = filter_release_dates(releases, since_text, until_text)

    if releases:
        shown, has_more = take_limited(releases, limit)
        click.echo(sub_heading("Recent Releases"))
        for r in shown:
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
            source = r.get("url") or github_url(owner, name, "releases", "tag", tag)
            click.echo(f"  Source: {source}")
        if has_more:
            click.echo(more_results_hint(limit))
