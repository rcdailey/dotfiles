"""GitHub repository exploration and workflow commands."""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Explore GitHub repositories and workflows."""


# Submodules attach their commands to `cli` on import.
from research.scout import explore, issues, commits, synthesis  # noqa: E402,F401
