---
name: python-scripting
description: >-
  Use when creating, editing, refactoring, or reviewing modularized Python CLI scripts managed by
  uv with pyproject.toml; scaffolding new script projects; adding commands or subcommands to
  Click-based CLIs; writing pytest tests for CLI tools; configuring hatchling builds or dependency
  groups; creating wrapper shell scripts for uv-managed projects. Triggers on phrases like "new
  python script", "add a CLI command", "scaffold a script project", "python CLI", "click command",
  or any work in a scripts/ directory containing pyproject.toml with hatchling. Do NOT use for
  single-file scripts, Jupyter notebooks, web applications, or Django/Flask projects.
---

# Python Script Projects

Modularized Python CLI scripts: self-contained projects managed by uv, built with hatchling, Click
for command routing. The sole audience is LLMs; never humans.

## Philosophy

These scripts are means to an end. They serve LLMs. Refactor mercilessly. Do not constrain changes
by scope, backward compatibility, or conservatism. A proper end result matters more than a minimal
diff. If touching a file reveals violations or suboptimal patterns, fix them regardless of whether
they relate to the original task.

## Project Structure

```txt
project-name/
  pyproject.toml
  uv.lock              # committed; deterministic installs
  package_name/
    __init__.py        # __version__ = "0.1.0"
    __main__.py        # from package_name.cli import cli; cli()
    cli.py             # root Click group with auto-discovery
    _click.py          # HelpfulGroup class
    _errors.py         # die(), domain exceptions
    command_a.py       # exposes `cli` attribute (auto-discovered)
    _helpers.py        # underscore prefix = private, skipped by auto-discovery
    subgroup/          # nested command group (subpackage)
      __init__.py      # defines group, imports subcommand modules
      subcommand.py    # attaches to parent group via decorator
  tests/
    __init__.py
    conftest.py
    test_command_a.py
```

- Directory: kebab-case (`gh-review`). Package: snake_case equivalent (`gh_review`).
- Command modules: plain names matching the CLI subcommand (`web.py`, `pdf.py`).
- Every project uses the group pattern with auto-discovery, even single-command projects.

## pyproject.toml

Minimal, no unnecessary metadata. Hatchling build backend. Python 3.13+. Click always present.

```toml
[project]
name = "project-name"
version = "0.1.0"
description = "One-line description of what this CLI does"
requires-python = ">=3.13"
dependencies = ["click>=8.1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["package_name"]

[dependency-groups]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Rules:

- Click is always a dependency. No argparse. No exceptions.
- Minimum-version pins only (`>=X.Y`), not ranges or exact pins
- `[tool.hatch.build.targets.wheel] packages` MUST point to the package directory
- Dev tools in `[dependency-groups] dev` (not `[project.optional-dependencies]`)
- Omit license, authors, URLs, classifiers
- No `[project.scripts]`; use wrapper scripts (see Invocation)

## Invocation

Projects are invoked via thin shell wrappers that use `uv run --project`:

```bash
#!/usr/bin/env bash
exec uv run --quiet \
  --project "$(chezmoi source-path)/../scripts/project-name" \
  -m package_name "$@"
```

For non-chezmoi repos, resolve relative to the wrapper itself:

```bash
#!/usr/bin/env bash
exec uv run --quiet \
  --project "$(dirname "$(realpath "$0")")/../scripts/project-name" \
  -m package_name "$@"
```

## Click Patterns

### Root Group with Auto-Discovery

Any module in the package exposing a `cli` attribute (`click.Command` or `click.Group`) is
registered automatically as a subcommand.

```python
"""Root CLI group with auto-discovery of subcommand modules."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import click

from package_name._click import HelpfulGroup


class _AutoGroup(HelpfulGroup):
    """Click group that auto-discovers subcommand modules.

    Any module in the package that exposes a ``cli`` attribute
    (a click.Group or click.Command) is registered as a subcommand.
    Modules whose names start with ``_`` are skipped (private helpers).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded = False

    def _load_plugins(self):
        if self._loaded:
            return
        self._loaded = True
        pkg_path = str(Path(__file__).parent)
        for info in pkgutil.iter_modules([pkg_path]):
            if info.name.startswith("_") or info.name == "cli":
                continue
            try:
                mod = importlib.import_module(f"package_name.{info.name}")
            except Exception:
                continue
            cmd = getattr(mod, "cli", None)
            if isinstance(cmd, click.Command):
                self.add_command(cmd, info.name)

    def list_commands(self, ctx):
        self._load_plugins()
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name):
        self._load_plugins()
        return super().get_command(ctx, cmd_name)


@click.group(
    cls=_AutoGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    version=__import__("package_name").__version__, prog_name="project-name"
)
def cli():
    """One-line description matching pyproject.toml."""
```

### HelpfulGroup (`_click.py`, verbatim in every project)

```python
"""Custom Click classes that show full help on usage errors."""

from __future__ import annotations

import click


class HelpfulGroup(click.Group):
    """Click group that appends the failing command's help to usage errors."""

    def invoke(self, ctx: click.Context) -> None:
        try:
            return super().invoke(ctx)
        except click.UsageError as exc:
            if exc.ctx is not None:
                click.echo(exc.format_message(), err=True)
                click.echo("", err=True)
                click.echo(exc.ctx.get_help(), err=True)
            else:
                click.echo(exc.format_message(), err=True)
            raise SystemExit(exc.exit_code) from None
```

### Command Modules

Each command module exposes a `cli` attribute:

```python
"""Brief description of what this command does."""

from __future__ import annotations

import click


@click.command()
@click.argument("target")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
def cli(target: str, verbose: bool) -> None:
    """Verb-phrase describing the action."""
    ...
```

For command groups (subpackages), the `__init__.py` defines the group and imports subcommands:

```python
"""Subgroup description."""

from __future__ import annotations

import click

from package_name._click import HelpfulGroup


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Verb-phrase describing the subgroup."""


from package_name.subgroup import sub_a, sub_b  # noqa: E402, F401
```

Subcommands attach to the parent group:

```python
from __future__ import annotations

import click

from package_name.subgroup import cli


@cli.command()
@click.argument("repo")
def sub_a(repo: str) -> None:
    """Verb-phrase describing this subcommand."""
    ...
```

### `__main__.py` (exact pattern, no variation)

```python
"""Entry point for `python -m package_name`."""

from package_name.cli import cli

if __name__ == "__main__":
    cli()
```

## Error Handling

### _errors.py

```python
"""Error types and fatal exit helper."""

from __future__ import annotations

import sys
from typing import NoReturn


class ToolError(Exception):
    """Domain-specific error (e.g., API failure, invalid input)."""


def die(message: str) -> NoReturn:
    """Print error to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)
```

Name the exception class after the domain (`FetchError`, `GhError`, `ApiError`). One per project is
typical; add more only when callers need to distinguish failure modes.

### Exception Flow

- Raise domain exceptions from helpers; catch at command level with `click.echo(..., err=True)` +
  `sys.exit(1)`
- Click handles `UsageError` (via `HelpfulGroup`), `KeyboardInterrupt`, `EOFError`,
  `BrokenPipeError`
- Exit codes: 0 success, 1 error, 2 usage (Click automatic)

## Output

LLM consumption only. Token efficiency is the primary constraint.

- `click.echo()` for all output. Never `print()` (except inside `die()`).
- Errors: `click.echo(..., err=True)`. Data: `click.echo(...)` to stdout.
- Default format is **prose**. Short sentences, no filler.
- NEVER JSON/YAML/tables unless a downstream tool requires machine-parseable input.
- NEVER colors, bold, ANSI escapes, spinners, progress bars, box-drawing, emoji.
- NEVER depend on rich, tabulate, colorama, tqdm, or similar.
- Truncate long output: `[truncated at N chars]`
- Help text and error messages: terse and informative, not friendly or decorative.

## Configuration

Environment variables for secrets/host config. CLI args for per-invocation settings. Hard-coded
defaults. No config files. Validate env vars early:

```python
"""Configuration from environment."""

from __future__ import annotations

import os

from package_name._errors import die


def require_env(name: str) -> str:
    """Return env var value or die with clear message."""
    value = os.environ.get(name)
    if not value:
        die(f"{name} is not set")
    return value
```

## Subprocess Wrappers

Typed helpers in private modules (`_kubectl.py`, `_gh.py`, etc.):

```python
"""Subprocess wrapper for external-tool."""

from __future__ import annotations

import shutil
import subprocess

from package_name._errors import ToolError, die


def check_deps() -> None:
    """Verify external tool is available. Called once at startup."""
    if not shutil.which("tool"):
        die("tool not found; install it first")


def run_tool(*args: str) -> str:
    """Run tool with args, return stdout. Raises ToolError on failure."""
    result = subprocess.run(["tool", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise ToolError(result.stderr.strip())
    return result.stdout
```

Call `check_deps()` from the root CLI group callback (the `cli()` function body in `cli.py`).

## Code Style

- `from __future__ import annotations` at the top of every module
- Type hints on all function signatures
- `NoReturn` for `die()` and similar
- Docstrings: module-level (one line), class-level (brief), public functions (brief)
- Private helpers: underscore-prefixed module names and function names
- No `if __name__ == "__main__"` in modules other than `__main__.py`
- Imports: stdlib, blank line, third-party, blank line, local (isort default)

## Testing

Tests use pytest with Click's `CliRunner`. Flat functions (no test classes). Mock at the subprocess
wrapper boundary (`run_tool`, `run_gh`, etc.), not deeper. Run via `uv run --project . pytest`.

```python
from unittest.mock import patch

from click.testing import CliRunner

from package_name.cli import cli


def test_command_success():
    runner = CliRunner()
    result = runner.invoke(cli, ["command", "arg"])
    assert result.exit_code == 0
    assert "expected output" in result.output


def test_command_with_external_tool():
    with patch("package_name._tool.run_tool", return_value="output"):
        runner = CliRunner()
        result = runner.invoke(cli, ["fetch", "target"])
        assert result.exit_code == 0
```

## Compliance Checklist

Every script project MUST pass all items below at all times. Verify after creating, editing,
refactoring, or reviewing any project. Fix violations in place.

### Structure

- [ ] Directory is kebab-case; package is snake_case equivalent
- [ ] `pyproject.toml` present with hatchling build backend
- [ ] `uv.lock` present and committed
- [ ] Package contains `__init__.py` with `__version__`
- [ ] Package contains `__main__.py` with exact entry pattern
- [ ] Package contains `_click.py` with `HelpfulGroup` (verbatim)
- [ ] Package contains `_errors.py` with `die()` and domain exception
- [ ] Package contains `cli.py` with `_AutoGroup` root group
- [ ] `tests/` directory exists with `__init__.py` and at least one test file
- [ ] No `[project.scripts]` in pyproject.toml; wrapper script exists instead

### Dependencies

- [ ] `requires-python = ">=3.13"`
- [ ] Click is listed in dependencies (no argparse usage anywhere)
- [ ] All pins use `>=X.Y` format
- [ ] Dev dependencies in `[dependency-groups] dev`, not `[project.optional-dependencies]`
- [ ] No formatting/UI libraries (rich, tabulate, colorama, tqdm, etc.)

### Code

- [ ] Every `.py` file starts with `from __future__ import annotations`
- [ ] All function signatures have type hints
- [ ] `die()` typed as `NoReturn`
- [ ] All output uses `click.echo()`, never `print()` (except inside `die()`)
- [ ] Errors go to stderr via `click.echo(..., err=True)`
- [ ] No JSON/YAML/table output unless a downstream tool requires it
- [ ] No ANSI colors, emoji, or decorative formatting in output
- [ ] Private modules prefixed with `_`
- [ ] No `if __name__ == "__main__"` except in `__main__.py`
- [ ] External tool dependencies checked via `check_deps()` at startup
- [ ] Subprocess calls wrapped in typed helper functions in private modules

### Testing

- [ ] pytest configured in `[tool.pytest.ini_options]`
- [ ] Tests use flat functions (no test classes)
- [ ] CLI tests use `click.testing.CliRunner`
- [ ] External calls mocked at the subprocess wrapper boundary
- [ ] `uv run --project . pytest` passes
