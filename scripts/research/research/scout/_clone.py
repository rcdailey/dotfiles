"""Local repo clone management with lazy clone and staleness refresh."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import click

CLONE_BASE = Path("/tmp/research-repos")
STALE_SECONDS = 3600  # 1 hour
MARKER = ".last_fetched"


def _repo_dir(owner: str, repo: str) -> Path:
    return CLONE_BASE / owner / repo


def ensure_repo(owner: str, repo: str) -> Path:
    """Ensure repo is cloned and fresh; return local path.

    First call clones with ``--depth 1``.  Subsequent calls check the
    ``.last_fetched`` marker and pull when older than ``STALE_SECONDS``.
    """
    repo_dir = _repo_dir(owner, repo)
    marker = repo_dir / MARKER

    if repo_dir.exists():
        if marker.exists():
            age = time.time() - marker.stat().st_mtime
            if age > STALE_SECONDS:
                click.echo(
                    f"[updating {owner}/{repo} (stale: {int(age)}s)]",
                    err=True,
                )
                result = subprocess.run(
                    ["git", "pull", "--ff-only", "-q"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    click.echo(
                        f"warning: git pull failed: {result.stderr.strip()}",
                        err=True,
                    )
                marker.touch()
        else:
            marker.touch()
        return repo_dir

    click.echo(f"[cloning {owner}/{repo}]", err=True)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "-q",
            f"https://github.com/{owner}/{repo}.git",
            str(repo_dir),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"error: clone failed: {result.stderr.strip()}", err=True)
        sys.exit(1)
    marker.touch()
    return repo_dir
