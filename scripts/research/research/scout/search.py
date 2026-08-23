"""Repository search across GitHub."""

from __future__ import annotations

import json

import click

from research._ghapi import APIError, _run_gh, api
from research._render import DEFAULT_SCOUT_MAX_CHARS, truncate_output
from research._source_ledger import record_visible_sources
from research.scout import cli
from research.scout._common import die, github_url, more_results_hint, take_limited

_SEARCH_FIELDS = (
    "fullName,url,stargazersCount,forksCount,pushedAt,updatedAt,isArchived,language,description"
)


def _search_repos(
    query: str, limit: int, sort: str, language: str | None, stars: int | None
) -> list[dict]:
    args = [
        "search",
        "repos",
        query,
        "--limit",
        str(limit),
        "--sort",
        sort,
        "--json",
        _SEARCH_FIELDS,
    ]
    if language:
        args.extend(["--language", language])
    if stars is not None:
        args.extend(["--stars", f">={stars}"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "gh search repos failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON response: {e}") from e


def _top_forks(full_name: str, count: int) -> list[dict]:
    return api(f"repos/{full_name}/forks", params={"sort": "stargazers", "per_page": str(count)})


def _render_result(repo: dict, forks: int) -> str:
    full_name = repo.get("fullName", "?")
    lines = [f"=== {full_name} ==="]
    description = repo.get("description") or "none"
    lines.extend(
        [
            f"description: {description}",
            f"language: {repo.get('language') or 'none'}",
            f"stars: {repo.get('stargazersCount', 0)}",
            f"forks: {repo.get('forksCount', 0)}",
            f"last push: {repo.get('pushedAt', 'unknown')[:10]}",
            f"last updated: {repo.get('updatedAt', 'unknown')[:10]}",
        ]
    )
    if repo.get("url"):
        lines.append(f"source: {repo['url']}")
    elif "/" in full_name:
        owner, name = full_name.split("/", 1)
        lines.append(f"source: {github_url(owner, name)}")
    if repo.get("isArchived"):
        lines.append("archived: true")

    if forks <= 0:
        return "\n".join(lines)

    try:
        top_forks = _top_forks(full_name, forks)
    except APIError as e:
        lines.append(f"forks: failed to fetch ({e})")
        return "\n".join(lines)

    if not top_forks:
        lines.append("top forks: none")
        return "\n".join(lines)

    lines.append("top forks:")
    for fork in top_forks:
        fork_name = fork.get("full_name", "?")
        fork_stars = fork.get("stargazers_count", 0)
        fork_pushed = (fork.get("pushed_at") or "unknown")[:10]
        lines.append(f"  {fork_name} (stars: {fork_stars}, last commit: {fork_pushed})")
    return "\n".join(lines)


@cli.command()
@click.argument("query")
@click.option("--limit", "-L", type=int, default=30, help="max results")
@click.option(
    "--sort",
    type=click.Choice(["stars", "forks", "updated"]),
    default="stars",
    help="sort order",
)
@click.option("--language", help="filter by language")
@click.option("--stars", type=int, help="minimum star count")
@click.option("--forks", type=int, default=0, help="show top N forks by stars per result")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def search(
    query: str,
    limit: int,
    sort: str,
    language: str | None,
    stars: int | None,
    forks: int,
    max_chars: int,
) -> None:
    """Search GitHub repositories."""
    try:
        results = _search_repos(query, limit + 1, sort, language, stars)
    except APIError as e:
        die(str(e))

    if not results:
        click.echo(f"No repositories found for query: {query}")
        return

    shown, has_more = take_limited(results, limit)
    sources = [
        repo.get("url") or github_url(*repo["fullName"].split("/", 1))
        for repo in shown
        if "/" in repo.get("fullName", "")
    ]
    output = "\n\n".join(_render_result(repo, forks) for repo in shown)
    if has_more:
        output += f"\n\n{more_results_hint(limit)}"
    rendered = truncate_output(
        output,
        max_chars,
        "reduce --limit or narrow the repository query",
    )
    record_visible_sources(rendered, sources)
    click.echo(rendered)
