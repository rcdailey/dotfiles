"""Shared helpers for scout subcommands."""

from __future__ import annotations

import click

from research._errors import die  # noqa: F401


def parse_repo(repo: str) -> tuple[str, str]:
    """Parse an OWNER/REPO string into (owner, repo)."""
    parts = repo.split("/")
    if len(parts) != 2:
        raise click.BadParameter(f"repo must be OWNER/REPO format, got: {repo}")
    return parts[0], parts[1]
