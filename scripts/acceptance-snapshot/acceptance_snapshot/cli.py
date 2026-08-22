"""Root CLI group with auto-discovery of subcommand modules."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import click

from acceptance_snapshot._click import HelpfulGroup
from acceptance_snapshot._git import check_git


class _AutoGroup(HelpfulGroup):
    """Discover command modules that expose a Click command."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded = False

    def _load_plugins(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        package_path = str(Path(__file__).parent)
        for info in pkgutil.iter_modules([package_path]):
            if info.name.startswith("_") or info.name == "cli":
                continue
            try:
                module = importlib.import_module(f"acceptance_snapshot.{info.name}")
            except Exception:  # noqa: BLE001,S112
                continue
            command = getattr(module, "cli", None)
            if isinstance(command, click.Command):
                self.add_command(command, info.name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        self._load_plugins()
        return super().list_commands(ctx)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        self._load_plugins()
        return super().get_command(ctx, cmd_name)


@click.group(
    cls=_AutoGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    version=__import__("acceptance_snapshot").__version__,
    prog_name="acceptance-snapshot",
)
def cli() -> None:
    """Capture and compare acceptance audit iterations."""
    check_git()
