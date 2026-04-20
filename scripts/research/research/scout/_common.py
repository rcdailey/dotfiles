"""Shared helpers for scout subcommands."""

from __future__ import annotations

import sys

import click


def parse_repo(repo: str) -> tuple[str, str]:
    """Parse an OWNER/REPO string into (owner, repo)."""
    parts = repo.split("/")
    if len(parts) != 2:
        raise click.BadParameter(f"repo must be OWNER/REPO format, got: {repo}")
    return parts[0], parts[1]


def die(msg: str, code: int = 1) -> None:
    """Print `error: <msg>` to stderr and exit."""
    click.echo(f"error: {msg}", err=True)
    sys.exit(code)
