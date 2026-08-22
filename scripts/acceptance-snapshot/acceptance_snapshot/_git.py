"""Git operations over private snapshot indexes and objects."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from acceptance_snapshot._errors import SnapshotError, die


def check_git() -> None:
    """Verify Git is available."""
    if not shutil.which("git"):
        die("git not found; install it first")


def _run(
    repository: Path,
    *args: str,
    environment: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise SnapshotError(message or f"git {' '.join(args)} failed")
    return result.stdout


def repository_root() -> Path:
    """Return the current repository root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SnapshotError(result.stderr.strip() or "not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def repository_objects(repository: Path) -> Path:
    """Return the repository's object directory."""
    value = _run(
        repository,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "objects",
    )
    return Path(value.strip())


def resolve_tree(repository: Path, revision: str) -> str:
    """Resolve a revision to its tree object."""
    return _run(repository, "rev-parse", "--verify", f"{revision}^{{tree}}").strip()


def _snapshot_environment(repository: Path, state_directory: Path) -> dict[str, str]:
    environment = os.environ.copy()
    alternates = [str(repository_objects(repository))]
    if existing := environment.get("GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        alternates.append(existing)
    environment.update(
        {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": os.pathsep.join(alternates),
            "GIT_OBJECT_DIRECTORY": str(state_directory / "objects"),
        }
    )
    return environment


def capture_tree(repository: Path, state_directory: Path, index_name: str) -> str:
    """Capture the nonignored filesystem state as a private Git tree."""
    index_path = state_directory / index_name
    index_path.unlink(missing_ok=True)
    (state_directory / f"{index_name}.lock").unlink(missing_ok=True)

    environment = _snapshot_environment(repository, state_directory)
    environment["GIT_INDEX_FILE"] = str(index_path)
    try:
        _run(repository, "read-tree", "HEAD", environment=environment)
        _run(repository, "add", "-A", "--", ".", environment=environment)
        return _run(repository, "write-tree", environment=environment).strip()
    finally:
        index_path.unlink(missing_ok=True)
        (state_directory / f"{index_name}.lock").unlink(missing_ok=True)


def changed_paths(
    repository: Path,
    state_directory: Path,
    previous_tree: str,
    current_tree: str,
) -> str:
    """Return Git's concise changed-path inventory between two trees."""
    environment = _snapshot_environment(repository, state_directory)
    return _run(
        repository,
        "diff",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--name-status",
        "--find-renames",
        previous_tree,
        current_tree,
        environment=environment,
    ).strip()


def tree_diff(
    repository: Path,
    state_directory: Path,
    previous_tree: str,
    current_tree: str,
    paths: tuple[str, ...],
) -> str:
    """Return a targeted Git patch between two snapshot trees."""
    environment = _snapshot_environment(repository, state_directory)
    return _run(
        repository,
        "diff",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--binary",
        "--full-index",
        "--find-renames",
        previous_tree,
        current_tree,
        "--",
        *paths,
        environment=environment,
    )
