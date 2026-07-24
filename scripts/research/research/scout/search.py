"""Repository search across GitHub."""

from __future__ import annotations

import json

import click

from research._ghapi import APIError, _run_gh, api
from research.scout import cli
from research.scout._common import die

_SEARCH_FIELDS = (
    "fullName,stargazersCount,forksCount,pushedAt,updatedAt,isArchived,language,description"
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


def _render_result(repo: dict, forks: int) -> None:
    full_name = repo.get("fullName", "?")
    click.echo(f"=== {full_name} ===")
    description = repo.get("description") or "none"
    click.echo(f"description: {description}")
    click.echo(f"language: {repo.get('language') or 'none'}")
    click.echo(f"stars: {repo.get('stargazersCount', 0)}")
    click.echo(f"forks: {repo.get('forksCount', 0)}")
    click.echo(f"last push: {repo.get('pushedAt', 'unknown')[:10]}")
    click.echo(f"last updated: {repo.get('updatedAt', 'unknown')[:10]}")
    if repo.get("isArchived"):
        click.echo("archived: true")

    if forks <= 0:
        return

    try:
        top_forks = _top_forks(full_name, forks)
    except APIError as e:
        click.echo(f"forks: failed to fetch ({e})")
        return

    if not top_forks:
        click.echo("top forks: none")
        return

    click.echo("top forks:")
    for fork in top_forks:
        fork_name = fork.get("full_name", "?")
        fork_stars = fork.get("stargazers_count", 0)
        fork_pushed = (fork.get("pushed_at") or "unknown")[:10]
        click.echo(f"  {fork_name} (stars: {fork_stars}, last commit: {fork_pushed})")


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
def search(
    query: str,
    limit: int,
    sort: str,
    language: str | None,
    stars: int | None,
    forks: int,
) -> None:
    """Search GitHub repositories."""
    try:
        results = _search_repos(query, limit, sort, language, stars)
    except APIError as e:
        die(str(e))

    if not results:
        click.echo(f"No repositories found for query: {query}")
        return

    for i, repo in enumerate(results):
        if i:
            click.echo("")
        _render_result(repo, forks)
