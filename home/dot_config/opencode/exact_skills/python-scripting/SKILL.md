---
name: python-scripting
description: >-
  Use when creating, editing, or reviewing this dotfiles repository's uv-managed Python CLI projects
  under scripts/, or explicitly LLM-facing tooling using the same wrapper convention. Covers Click
  commands, hatchling packaging, and wrappers. Do not apply to arbitrary human-facing Python CLIs,
  single-file scripts, notebooks, or web applications.
---

# Python Script Projects

Modularized Python CLI scripts: self-contained projects managed by uv, built with hatchling, Click
for command routing. The sole audience is LLMs; never humans.

## Philosophy

These scripts serve LLM workflows. Prefer a coherent end state over preserving obsolete internal
structure. Refactor affected code when needed to remove duplication, inconsistency, or dead
indirection. Keep unrelated cleanup separate.

## Project Structure

```txt
project-name/
  pyproject.toml
  uv.lock              # committed; deterministic installs
  package_name/
    __init__.py        # __version__ = "0.1.0"
    __main__.py        # from package_name.cli import cli; cli()
    cli.py             # Click command or explicit group registration
    _click.py          # HelpfulGroup class
    _errors.py         # die(), domain exceptions
    command_a.py       # exposes a command for explicit registration
    _helpers.py        # underscore prefix = private
    subgroup/          # nested command group (subpackage)
      __init__.py      # defines group, imports subcommand modules
      subcommand.py    # attaches to parent group via decorator
```

- Directory: kebab-case (`gh-review`). Package: snake_case equivalent (`gh_review`).
- Command modules: plain names matching the CLI subcommand (`web.py`, `pdf.py`).
- Use a plain command for one operation and explicit group registration for multiple operations.
  Retain auto-discovery only when a current extension boundary needs it; never hide import failures.

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
```

Rules:

- Click is always a dependency. No argparse. No exceptions.
- Minimum-version pins only (`>=X.Y`), not ranges or exact pins
- `[tool.hatch.build.targets.wheel] packages` MUST point to the package directory
- Dev tools in `[dependency-groups] dev` (not `[project.optional-dependencies]`); omit the group
  entirely when there are none
- Put test tools in the dev dependency group when stable behavior needs regression coverage.
- Omit license, authors, URLs, classifiers
- No `[project.scripts]`; use wrapper scripts (see Invocation)

## Invocation

Projects are invoked via thin shell wrappers that use `uv run --project`:

```bash
#!/usr/bin/env bash
# Project-scoped vars from the caller's repo (mise commonly exports UV_PYTHON)
# would hijack this tool's interpreter. They arrive two ways: inherited through
# the environment, and re-injected by mise's uv shim from the caller's cwd.
exec env -u UV_PYTHON -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT \
  -u VIRTUAL_ENV -u PYTHONPATH -u PYTHONHOME MISE_NO_ENV=1 \
  uv run --quiet \
  --project "$(chezmoi source-path)/../scripts/project-name" \
  -m package_name "$@"
```

For non-chezmoi repos, resolve relative to the wrapper itself:

```bash
#!/usr/bin/env bash
exec env -u UV_PYTHON -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT \
  -u VIRTUAL_ENV -u PYTHONPATH -u PYTHONHOME MISE_NO_ENV=1 \
  uv run --quiet \
  --project "$(dirname "$(realpath "$0")")/../scripts/project-name" \
  -m package_name "$@"
```

The env prefix is mandatory. `uv` honors ambient `UV_*` regardless of `--project`, so a caller repo
pinning a Python older than the project's `requires-python` breaks the tool outright. `env -u` alone
is not enough when `uv` resolves to a mise shim: the shim reloads the caller's `mise.toml` and
re-injects `[env]` values, so `MISE_NO_ENV=1` is what neutralizes it.

## Click Patterns

### Explicit Command Registration

```python
"""Root CLI group."""

from __future__ import annotations

import click

from package_name._click import HelpfulGroup
from package_name.command_a import cli as command_a


@click.group(
    cls=HelpfulGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    version=__import__("package_name").__version__, prog_name="project-name"
)
def cli() -> None:
    """One-line description matching pyproject.toml."""


cli.add_command(command_a, "command-a")
```

### HelpfulGroup (`_click.py`, when a group needs expanded error help)

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

Call `check_deps()` from the entry command or group callback when external executables are required.

## Code Style

- `from __future__ import annotations` at the top of every module
- Type hints on all function signatures
- `NoReturn` for `die()` and similar
- Docstrings: module-level (one line), class-level (brief), public functions (brief)
- Private helpers: underscore-prefixed module names and function names
- No `if __name__ == "__main__"` in modules other than `__main__.py`
- Imports: stdlib, blank line, third-party, blank line, local (isort default)

## Verification

Apply the active testing policy to stable CLI behavior, especially mutations and recovery. Keep
durable behavioral tests when regressions would matter; use temporary probes for one-off details.

Back behavioral claims with executed checks. For temporary probes, exercise the real module inline
and discard the snippet afterward.

Every snippet MUST print the observed value next to the expectation, so pass/fail is in the output
rather than in your interpretation of a dump.

```sh
uv run --project . python - <<'EOF'
from package_name._helpers import parse_target
r = parse_target("owner/repo#12")
print("repo:", r.repo, "| number:", r.number, "| expect owner/repo, 12")
EOF
```

Choose the stable observable boundary that owns the behavior. For CLI contracts, invoke the command
the way its caller does:

```sh
uv run --project . -m package_name command arg
```

Output that contradicts the expectation MUST be diagnosed before any code change: re-derive the
expectation from the source, then suspect the harness, and only then the code. Synthetic drivers use
hand-built inputs, so anything ordering-, timing-, or environment-dependent needs a realistic
fixture; otherwise the harness reports its own artifacts as failures.

Scratch files MUST be deleted before reporting; when a file is unavoidable, name it `*.local.*`.

## Compliance Checklist

Check applicable items in the affected scope. During reviews, report violations without editing;
during implementation, fix only authorized scope. Do not retrofit unrelated projects or scaffolding.

### Structure

- [ ] Directory is kebab-case; package is snake_case equivalent
- [ ] `pyproject.toml` present with hatchling build backend
- [ ] `uv.lock` present and committed
- [ ] Package contains `__init__.py` with `__version__`
- [ ] Package contains `__main__.py` with exact entry pattern
- [ ] Groups use `HelpfulGroup` when expanded error help is needed
- [ ] Shared error helpers exist when multiple commands need them
- [ ] Command registration matches current complexity and surfaces import failures
- [ ] Stable, consequential behavior has regression coverage
- [ ] No `[project.scripts]` in pyproject.toml; wrapper script exists instead

### Dependencies

- [ ] `requires-python = ">=3.13"`
- [ ] Click is listed in dependencies (no argparse usage anywhere)
- [ ] All pins use `>=X.Y` format
- [ ] Dev dependencies in `[dependency-groups] dev`, not `[project.optional-dependencies]`
- [ ] No formatting/UI libraries (rich, tabulate, colorama, tqdm, etc.)
- [ ] Test dependencies, when needed, are development-only

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

### Verification

- [ ] Behavioral claims proven by an executed snippet, not reasoning
- [ ] Snippets print observed value beside expectation
- [ ] Scratch files deleted before reporting
