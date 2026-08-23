"""Issues, pull requests, and releases."""

from __future__ import annotations

import datetime

import click

from research._ghapi import (
    APIError,
    list_discussions,
    list_issues,
    list_prs,
    list_releases,
    view_discussion,
    view_issue,
    view_pr,
    view_release,
)
from research._render import (
    DEFAULT_SCOUT_MAX_CHARS,
    format_comment,
    format_issue_body,
    format_list_item,
    section_heading,
    truncate_output,
)
from research._source_ledger import record_sources, record_visible_sources
from research.scout import cli
from research.scout._common import (
    date_text,
    die,
    filter_release_dates,
    github_url,
    more_results_hint,
    parse_repo,
    take_limited,
)


def _format_comments(comments: list[dict], heading: str = "Comments") -> str:
    """Return comments as a Markdown section."""
    if not comments:
        return ""
    parts = [section_heading(heading)]
    for c in comments:
        author = c.get("author", {}).get("login", "unknown")
        parts.append(format_comment(author, c.get("createdAt", ""), c.get("body", "")))
    return "\n\n".join(parts)


@cli.command()
@click.argument("repo")
@click.argument("number", required=False)
@click.option("--search", "-S", help="search query")
@click.option("--state", "-s", default="open", type=click.Choice(["open", "closed", "all"]))
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
@click.option("--comments", is_flag=True, help="include comments when viewing one issue")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def issue(
    repo: str,
    number: str | None,
    search: str | None,
    state: str,
    limit: int,
    comments: bool,
    max_chars: int,
) -> None:
    """List or view issues."""
    owner, name = parse_repo(repo)

    if number:
        try:
            n = int(number)
        except ValueError:
            raise click.UsageError(f"invalid issue number: {number}")
        try:
            data = view_issue(owner, name, n, include_comments=comments)
        except APIError as e:
            die(str(e))
        source = data.get("url") or github_url(owner, name, "issues", n)
        output = format_issue_body(
            data["number"],
            data.get("title", "N/A"),
            data.get("state", "unknown"),
            data.get("createdAt", ""),
            data.get("body", ""),
            source,
        )
        if comments:
            output += _format_comments(data.get("comments", []))
        rendered = truncate_output(
            output,
            max_chars,
            "omit --comments or use a narrower source",
        )
        record_visible_sources(rendered, [source])
        click.echo(rendered)
        return

    try:
        issues = list_issues(owner, name, state, search, limit + 1)
    except APIError as e:
        die(str(e))
    if not issues:
        click.echo(f"No issues found in {repo} (state: {state})")
        return
    shown, has_more = take_limited(issues, limit)
    record_sources(
        item.get("url") or github_url(owner, name, "issues", item["number"]) for item in shown
    )
    for i in shown:
        click.echo(
            format_list_item(
                i["number"],
                i["state"],
                i.get("createdAt", ""),
                i.get("title", "N/A"),
                source_url=i.get("url") or github_url(owner, name, "issues", i["number"]),
            )
        )
    if has_more:
        click.echo(more_results_hint(limit))


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
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
@click.option("--comments", is_flag=True, help="include comments when viewing one PR")
@click.option("--reviews", is_flag=True, help="include reviews when viewing one PR")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def pr(
    repo: str,
    number: str | None,
    search: str | None,
    state: str,
    limit: int,
    comments: bool,
    reviews: bool,
    max_chars: int,
) -> None:
    """List or view pull requests."""
    owner, name = parse_repo(repo)

    if number:
        try:
            n = int(number)
        except ValueError:
            raise click.UsageError(f"invalid PR number: {number}")
        try:
            data = view_pr(
                owner,
                name,
                n,
                include_comments=comments,
                include_reviews=reviews,
            )
        except APIError as e:
            die(str(e))

        merged_at = data.get("mergedAt")
        state_str = data.get("state", "unknown")
        if merged_at:
            state_str += f" (merged {merged_at[:10]})"

        source = data.get("url") or github_url(owner, name, "pull", n)
        output = format_issue_body(
            data["number"],
            data.get("title", "N/A"),
            state_str,
            data.get("createdAt", ""),
            data.get("body", ""),
            source,
        )
        if comments:
            output += _format_comments(data.get("comments", []))

        review_items = data.get("reviews", []) if reviews else []
        if review_items:
            output += section_heading("Reviews")
            for r in review_items:
                author = r.get("author", {}).get("login", "unknown")
                rstate = r.get("state", "unknown")
                output += f"\n**@{author} ({rstate}):**\n\n{r.get('body', '')}\n"
        rendered = truncate_output(
            output,
            max_chars,
            "omit --comments/--reviews or use a narrower source",
        )
        record_visible_sources(rendered, [source])
        click.echo(rendered)
        return

    try:
        prs = list_prs(owner, name, state, search, limit + 1)
    except APIError as e:
        die(str(e))
    if not prs:
        click.echo(f"No PRs found in {repo} (state: {state})")
        return
    shown, has_more = take_limited(prs, limit)
    record_sources(
        item.get("url") or github_url(owner, name, "pull", item["number"]) for item in shown
    )
    for p in shown:
        label = p["state"]
        if p.get("mergedAt"):
            label += " (merged)"
        click.echo(
            format_list_item(
                p["number"],
                label,
                p.get("createdAt", p.get("mergedAt", "")),
                p.get("title", "N/A"),
                source_url=p.get("url") or github_url(owner, name, "pull", p["number"]),
            )
        )
    if has_more:
        click.echo(more_results_hint(limit))


@cli.command()
@click.argument("repo")
@click.argument("tag", required=False)
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
@click.option("--since", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option("--until", type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def release(
    repo: str,
    tag: str | None,
    limit: int,
    since: datetime.datetime | None,
    until: datetime.datetime | None,
    max_chars: int,
) -> None:
    """List or view releases."""
    owner, name = parse_repo(repo)

    if tag:
        if since or until:
            raise click.UsageError("TAG cannot be combined with --since or --until")
        try:
            data = view_release(owner, name, tag)
        except APIError as e:
            die(str(e))
        lines = [f"## Release: {data.get('tagName', tag)}\n"]
        if data.get("name"):
            lines.append(f"**Name:** {data['name']}")
        if data.get("publishedAt"):
            lines.append(f"**Published:** {data['publishedAt'][:10]}")
        if data.get("author"):
            lines.append(f"**Author:** @{data['author'].get('login', 'unknown')}")
        source = data.get("url") or github_url(owner, name, "releases", "tag", tag)
        lines.append(f"**Source:** {source}")
        if data.get("body"):
            lines.extend(["", data["body"]])
        rendered = truncate_output(
            "\n".join(lines),
            max_chars,
            "use the release's linked PRs or commits for narrower evidence",
        )
        record_visible_sources(rendered, [source])
        click.echo(rendered)
        return

    since_text = date_text(since)
    until_text = date_text(until)
    if since_text and until_text and since_text > until_text:
        raise click.UsageError("--since must not be after --until")
    fetch_limit = 1000 if since_text or until_text else limit + 1
    try:
        releases = list_releases(owner, name, fetch_limit)
    except APIError as e:
        die(str(e))
    if not releases:
        click.echo(f"No releases found in {repo}")
        return
    releases = filter_release_dates(releases, since_text, until_text)
    if not releases:
        click.echo("No releases found for the requested range")
        return
    shown, has_more = take_limited(releases, limit)
    record_sources(
        item.get("url") or github_url(owner, name, "releases", "tag", item.get("tagName", "N/A"))
        for item in shown
    )
    for r in shown:
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
        source = r.get("url") or github_url(owner, name, "releases", "tag", tag_name)
        click.echo(f"{line}\n  Source: {source}")
    if has_more:
        click.echo(more_results_hint(limit))


@cli.command()
@click.argument("repo")
@click.argument("number", required=False)
@click.option("--search", "-S", help="search query (filters by title)")
@click.option("--limit", "-L", type=click.IntRange(min=1), default=30)
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def discussion(
    repo: str,
    number: str | None,
    search: str | None,
    limit: int,
    max_chars: int,
) -> None:
    """List or view GitHub Discussions."""
    owner, name = parse_repo(repo)

    if number:
        try:
            n = int(number)
        except ValueError:
            raise click.UsageError(f"invalid discussion number: {number}")
        try:
            data = view_discussion(owner, name, n)
        except APIError as e:
            die(str(e))
        category = data.get("category", {}).get("name", "")
        cat_str = f" [{category}]" if category else ""
        source = data.get("url") or github_url(owner, name, "discussions", n)
        output = format_issue_body(
            data["number"],
            data.get("title", "N/A") + cat_str,
            "open",
            data.get("createdAt", ""),
            data.get("body", ""),
            source,
        )
        output += _format_comments(data.get("comments", []))
        rendered = truncate_output(
            output,
            max_chars,
            "use the discussion body or comments as separate narrower evidence",
        )
        record_visible_sources(rendered, [source])
        click.echo(rendered)
        return

    try:
        discussions = list_discussions(owner, name, search, limit + 1)
    except APIError as e:
        die(str(e))
    if not discussions:
        click.echo(f"No discussions found in {repo}")
        return
    shown, has_more = take_limited(discussions, limit)
    record_sources(
        item.get("url") or github_url(owner, name, "discussions", item["number"]) for item in shown
    )
    for d in shown:
        category = d.get("category", {}).get("name", "")
        cat_str = f" [{category}]" if category else ""
        click.echo(
            format_list_item(
                d["number"],
                category or "discussion",
                d.get("createdAt", ""),
                d.get("title", "N/A"),
                source_url=d.get("url") or github_url(owner, name, "discussions", d["number"]),
            )
        )
    if has_more:
        click.echo(more_results_hint(limit))
