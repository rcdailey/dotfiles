"""Local repo clone management with lazy clone and staleness refresh."""

from __future__ import annotations

import contextlib
import fcntl
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path

import click

CLONE_BASE = Path("/tmp/research-repos")
STALE_SECONDS = 3600  # 1 hour
MARKER = ".last_fetched"


def _repo_dir(owner: str, repo: str) -> Path:
    return CLONE_BASE / owner / repo


@contextlib.contextmanager
def _repo_lock(owner: str, repo: str) -> Generator[None, None, None]:
    """Exclusive per-repo flock. Held only during mutations."""
    lock_file = CLONE_BASE / owner / f"{repo}.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_file, "w")  # noqa: SIM115
    try:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
        fp.close()


def _do_clone(repo_dir: Path, owner: str, repo: str) -> None:
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
    (repo_dir / MARKER).touch()


def _do_pull_if_stale(repo_dir: Path, owner: str, repo: str) -> None:
    marker = repo_dir / MARKER
    if not marker.exists():
        marker.touch()
        return
    age = time.time() - marker.stat().st_mtime
    if age <= STALE_SECONDS:
        return
    click.echo(f"[updating {owner}/{repo} (stale: {int(age)}s)]", err=True)
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


def _is_ready(repo_dir: Path) -> bool:
    """True when clone is complete (marker exists)."""
    return (repo_dir / MARKER).exists()


def ensure_repo(owner: str, repo: str) -> Path:
    """Ensure repo is cloned and fresh; return local path.

    First call clones with ``--depth 1``.  Subsequent calls check the
    ``.last_fetched`` marker and pull when older than ``STALE_SECONDS``.
    Mutations are protected by a per-repo flock so parallel callers
    serialize only during clone/pull.

    Readiness is determined by the marker file, not directory existence,
    because ``git clone`` creates the target directory before it finishes
    populating files.
    """
    repo_dir = _repo_dir(owner, repo)

    if _is_ready(repo_dir):
        marker = repo_dir / MARKER
        age = time.time() - marker.stat().st_mtime
        if age > STALE_SECONDS:
            with _repo_lock(owner, repo):
                _do_pull_if_stale(repo_dir, owner, repo)
        return repo_dir

    # Clone needed; re-check under lock (another process may have won).
    with _repo_lock(owner, repo):
        if not _is_ready(repo_dir):
            _do_clone(repo_dir, owner, repo)
    return repo_dir


def ensure_ref(owner: str, repo: str, ref: str) -> str:
    """Ensure ``ref`` is available locally and return the resolved SHA.

    Checks whether the ref resolves before fetching to avoid unnecessary
    network calls. The fetch (if needed) is protected by a per-repo flock.
    """
    repo_dir = ensure_repo(owner, repo)

    # Try resolving without fetch first (read-only, no lock needed).
    sha = _try_resolve(repo_dir, ref)
    if sha:
        return sha

    # Fetch the ref, then resolve. Only use FETCH_HEAD if fetch succeeds.
    with _repo_lock(owner, repo):
        result = subprocess.run(
            ["git", "fetch", "--depth=1", "origin", ref],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        click.echo(f"error: ref not found: {ref}", err=True)
        sys.exit(1)

    # After successful fetch, try the ref again and FETCH_HEAD.
    sha = _try_resolve(repo_dir, ref)
    if sha:
        return sha
    sha = _resolve_one(repo_dir, "FETCH_HEAD")
    if sha:
        return sha
    click.echo(f"error: could not resolve ref: {ref}", err=True)
    sys.exit(1)


def _try_resolve(repo_dir: Path, ref: str) -> str | None:
    """Attempt to resolve ref to a SHA. Does NOT try FETCH_HEAD."""
    for candidate in (ref, f"origin/{ref}"):
        sha = _resolve_one(repo_dir, candidate)
        if sha:
            return sha
    return None


def _resolve_one(repo_dir: Path, ref: str) -> str | None:
    """Resolve a single ref candidate to a SHA, or None."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None
