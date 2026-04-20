"""Issues, pull requests, and releases."""

from __future__ import annotations

import click

from research._budget import budget_reserve
from research._cache import get_cache
from research._ghapi import (
    APIError,
    list_issues,
    list_prs,
    list_releases,
    view_issue,
    view_pr,
    view_release,
)
from research._render import (
    format_comment,
    format_issue_body,
    format_list_item,
    section_heading,
)
from research.scout import cli
from research.scout._common import die, parse_repo


def _render_comments(comments: list[dict], heading: str = "Comments") -> None:
    if not comments:
        return
    click.echo(section_heading(heading))
    for c in comments:
        author = c.get("author", {}).get("login", "unknown")
        click.echo(format_comment(author, c.get("createdAt", ""), c.get("body", "")))
        click.echo("")


@cli.command()
@click.argument("repo")
@click.argument("number", required=False)
@click.option("--search", "-S", help="search query")
@click.option("--state", "-s", default="open", type=click.Choice(["open", "closed", "all"]))
@click.option("--limit", "-L", type=int, default=30)
def issue(repo: str, number: str | None, search: str | None, state: str, limit: int) -> None:
    """List or view issues."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    if number:
        try:
            n = int(number)
        except ValueError:
            die(f"invalid issue number: {number}", code=2)
        try:
            data = view_issue(owner, name, n)
        except APIError as e:
            die(str(e))
        click.echo(
            format_issue_body(
                data["number"],
                data.get("title", "N/A"),
                data.get("state", "unknown"),
                data.get("createdAt", ""),
                data.get("body", ""),
            )
        )
        _render_comments(data.get("comments", []))
        return

    try:
        issues = list_issues(owner, name, state, search, limit)
    except APIError as e:
        die(str(e))
    if not issues:
        click.echo(f"No issues found in {repo} (state: {state})")
        return
    for i in issues:
        click.echo(
            format_list_item(i["number"], i["state"], i.get("createdAt", ""), i.get("title", "N/A"))
        )


@cli.command()
@click.argument("repo")
@click.argument("number", required=False)
@click.option("--search", "-S", help="search query")
@click.option(
    "--state",
    "-s",
    default="open",
    type=click.Choice(["open", "closed", "merged", "all"]),
)
@click.option("--limit", "-L", type=int, default=30)
def pr(repo: str, number: str | None, search: str | None, state: str, limit: int) -> None:
    """List or view pull requests."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    if number:
        try:
            n = int(number)
        except ValueError:
            die(f"invalid PR number: {number}", code=2)
        try:
            data = view_pr(owner, name, n)
        except APIError as e:
            die(str(e))

        merged_at = data.get("mergedAt")
        state_str = data.get("state", "unknown")
        if merged_at:
            state_str += f" (merged {merged_at[:10]})"

        click.echo(
            format_issue_body(
                data["number"],
                data.get("title", "N/A"),
                state_str,
                data.get("createdAt", ""),
                data.get("body", ""),
            )
        )
        _render_comments(data.get("comments", []))

        reviews = data.get("reviews", [])
        if reviews:
            click.echo(section_heading("Reviews"))
            for r in reviews:
                author = r.get("author", {}).get("login", "unknown")
                rstate = r.get("state", "unknown")
                click.echo(f"**@{author} ({rstate}):**\n\n{r.get('body', '')}")
                click.echo("")
        return

    try:
        prs = list_prs(owner, name, state, search, limit)
    except APIError as e:
        die(str(e))
    if not prs:
        click.echo(f"No PRs found in {repo} (state: {state})")
        return
    for p in prs:
        label = p["state"]
        if p.get("mergedAt"):
            label += " (merged)"
        click.echo(
            format_list_item(
                p["number"],
                label,
                p.get("createdAt", p.get("mergedAt", "")),
                p.get("title", "N/A"),
            )
        )


@cli.command()
@click.argument("repo")
@click.argument("tag", required=False)
@click.option("--limit", "-L", type=int, default=30)
def release(repo: str, tag: str | None, limit: int) -> None:
    """List or view releases."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    if tag:
        try:
            data = view_release(owner, name, tag)
        except APIError as e:
            die(str(e))
        click.echo(f"## Release: {data.get('tagName', tag)}\n")
        if data.get("name"):
            click.echo(f"**Name:** {data['name']}")
        if data.get("publishedAt"):
            click.echo(f"**Published:** {data['publishedAt'][:10]}")
        if data.get("author"):
            click.echo(f"**Author:** @{data['author'].get('login', 'unknown')}")
        click.echo("")
        if data.get("body"):
            click.echo(data["body"])
        return

    try:
        releases = list_releases(owner, name, limit)
    except APIError as e:
        die(str(e))
    if not releases:
        click.echo(f"No releases found in {repo}")
        return
    for r in releases:
        tag_name = r.get("tagName", "N/A")
        published = r.get("publishedAt", "")[:10] if r.get("publishedAt") else "N/A"
        flags = []
        if r.get("isDraft"):
            flags.append("draft")
        if r.get("isPrerelease"):
            flags.append("pre-release")
        flag_str = f" ({', '.join(flags)})" if flags else ""
        line = f"- {tag_name}{flag_str} ({published})"
        if r.get("name"):
            line += f" {r['name']}"
        click.echo(line)
