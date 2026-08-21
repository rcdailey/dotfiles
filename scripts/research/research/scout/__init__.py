"""GitHub repository exploration and workflow commands."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

import click

from research._cache import get_cache
from research._click import HelpfulGroup
from research._ghapi import check_deps
from research._scout_budget import scout_budget_reserve


def _budgeted(callback: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(callback)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        context = click.get_current_context()
        parent = context.parent
        critical = bool(parent and parent.params.get("critical"))
        check_deps()
        scout_budget_reserve(get_cache(), critical=critical)
        return callback(*args, **kwargs)

    return wrapper


class _ScoutGroup(HelpfulGroup):
    def add_command(self, cmd: click.Command, name: str | None = None) -> None:
        if cmd.callback is not None:
            cmd.callback = _budgeted(cmd.callback)
        super().add_command(cmd, name)


@click.group(cls=_ScoutGroup)
@click.option("--critical", is_flag=True, help="use a reserved post-warning scout call")
def cli(critical: bool) -> None:
    """Explore GitHub repositories and workflows."""


# Submodules attach their commands to `cli` on import.
from research.scout import commits, explore, issues, local, search, synthesis  # noqa: F401
