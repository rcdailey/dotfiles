"""GitHub repository exploration and workflow commands."""

from __future__ import annotations

import click

from research._click import RecursiveHelpGroup
from research._ghapi import check_deps


@click.group(cls=RecursiveHelpGroup)
def cli() -> None:
    """Explore GitHub repositories and workflows."""
    check_deps()


# Submodules attach their commands to `cli` on import.
from research.scout import commits, explore, issues, local, search, synthesis  # noqa: F401
