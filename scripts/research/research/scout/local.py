"""Local clone exploration: rg, find, cat."""

from __future__ import annotations

import fnmatch
import subprocess
import sys

import click

from research.scout import cli
from research.scout._clone import ensure_ref, ensure_repo
from research.scout._common import parse_repo


@cli.command(name="rg")
@click.argument("repo")
@click.argument("pattern")
@click.option("--path", default=".", help="subdirectory to search within")
@click.option("--glob", "-g", "globs", multiple=True, help="file glob filter (repeatable)")
@click.option("--type", "filetype", help="ripgrep type filter (e.g., py, ts, go)")
@click.option("--context", "-C", type=int, default=0, help="lines of context around matches")
@click.option("--ignore-case", "-i", is_flag=True, help="case-insensitive search")
@click.option("--ref", help="branch, tag, or SHA (uses git grep)")
def rg_cmd(
    repo: str,
    pattern: str,
    path: str,
    globs: tuple[str, ...],
    filetype: str | None,
    context: int,
    ignore_case: bool,
    ref: str | None,
) -> None:
    """Search cloned repo with ripgrep (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        # git grep [opts] -e PATTERN REV [-- pathspec...]
        args = ["git", "grep", "--line-number", "--no-color"]
        if ignore_case:
            args.append("-i")
        if context > 0:
            args.append(f"-C{context}")
        args.extend(["-e", pattern, sha])
        # Pathspecs go after -- separator
        pathspecs: list[str] = []
        if path and path != ".":
            pathspecs.append(path)
        for g in globs:
            pathspecs.append(g)
        if filetype:
            # Map ripgrep --type to glob (e.g., "cs" -> "*.cs")
            pathspecs.append(f"*.{filetype}")
        if pathspecs:
            args.append("--")
            args.extend(pathspecs)
        result = subprocess.run(args, capture_output=True, text=True, cwd=repo_dir)
    else:
        args = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color=never",
            "--max-columns=200",
            "--max-columns-preview",
        ]
        if ignore_case:
            args.append("--ignore-case")
        if filetype:
            args.append(f"--type={filetype}")
        for g in globs:
            args.extend(["--glob", g])
        if context > 0:
            args.extend(["-C", str(context)])
        args.extend([pattern, path])
        result = subprocess.run(args, capture_output=True, text=True, cwd=repo_dir)

    if result.returncode == 0:
        click.echo(result.stdout, nl=False)
    elif result.returncode == 1:
        click.echo("no matches")
    else:
        click.echo(f"error: search failed: {result.stderr.strip()}", err=True)
        sys.exit(1)


@cli.command(name="find")
@click.argument("repo")
@click.argument("pattern")
@click.option("--limit", "-L", type=int, default=100, help="max results (0 = no limit)")
@click.option("--ref", help="branch, tag, or SHA (uses git ls-tree)")
def find_cmd(repo: str, pattern: str, limit: int, ref: str | None) -> None:
    """Find files in cloned repo by glob pattern (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", sha],
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        if result.returncode != 0:
            click.echo(f"error: git ls-tree failed: {result.stderr.strip()}", err=True)
            sys.exit(1)
        paths = [line for line in result.stdout.splitlines() if line]
        matches = sorted(
            p for p in paths if fnmatch.fnmatch(p, pattern) or fnmatch.fnmatch(p, f"*/{pattern}")
        )
    else:
        matches = sorted(
            p.relative_to(repo_dir) for p in repo_dir.rglob(pattern) if ".git" not in p.parts
        )

    if not matches:
        click.echo("no matches")
        return
    total = len(matches)
    if limit > 0:
        matches = matches[:limit]
    for m in matches:
        click.echo(m)
    if limit > 0 and total > limit:
        click.echo(f"\n... {total - limit} more matches (use --limit 0 to show all)")


@cli.command(name="cat")
@click.argument("repo")
@click.argument("path")
@click.option("--limit", "-L", type=int, default=0, help="max lines (0 = no limit)")
@click.option("--offset", type=int, default=0, help="skip first N lines")
@click.option("--ref", help="branch, tag, or SHA (uses git show)")
def cat_cmd(repo: str, path: str, limit: int, offset: int, ref: str | None) -> None:
    """Read file from cloned repo (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        result = subprocess.run(
            ["git", "show", f"{sha}:{path}"],
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            if "does not exist" in err or "Invalid object" in err:
                click.echo(f"error: file not found at ref {ref}: {path}", err=True)
            else:
                click.echo(f"error: could not read file: {err}", err=True)
            sys.exit(1)
        content = result.stdout
    else:
        file_path = repo_dir / path
        if not file_path.exists():
            click.echo(f"error: file not found: {path}", err=True)
            sys.exit(1)
        if not file_path.is_file():
            click.echo(f"error: not a file: {path}", err=True)
            sys.exit(1)

        try:
            content = file_path.read_text()
        except UnicodeDecodeError:
            click.echo(f"error: binary file: {path}", err=True)
            sys.exit(1)

    lines = content.split("\n")
    if offset:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]
    click.echo("\n".join(lines))
