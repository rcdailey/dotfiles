"""Shared helpers for scout subcommands."""

from __future__ import annotations

import datetime

import click

from research._errors import die  # noqa: F401


def parse_repo(repo: str) -> tuple[str, str]:
    """Parse an OWNER/REPO string into (owner, repo)."""
    parts = repo.split("/")
    if len(parts) != 2:
        raise click.BadParameter(f"repo must be OWNER/REPO format, got: {repo}")
    return parts[0], parts[1]


def github_url(owner: str, repo: str, *parts: object) -> str:
    """Return a canonical GitHub URL for a repository object."""
    suffix = "/".join(str(part).strip("/") for part in parts)
    base = f"https://github.com/{owner}/{repo}"
    return f"{base}/{suffix}" if suffix else base


def take_limited(items: list[dict], limit: int) -> tuple[list[dict], bool]:
    """Return at most limit items and whether additional items were available."""
    return items[:limit], len(items) > limit


def more_results_hint(limit: int) -> str:
    """Return a concise hint for a limited result set."""
    return f"... more results available; increase --limit above {limit}"


def date_text(value: datetime.datetime | None) -> str | None:
    """Return a Click date option as an ISO date string."""
    return value.strftime("%Y-%m-%d") if value else None


def filter_release_dates(releases: list[dict], since: str | None, until: str | None) -> list[dict]:
    """Return releases inside inclusive ISO date boundaries."""
    return [
        release
        for release in releases
        if (not since or (release.get("publishedAt") or "")[:10] >= since)
        and (not until or (release.get("publishedAt") or "")[:10] <= until)
    ]
