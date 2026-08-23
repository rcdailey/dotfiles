"""Local clone exploration: rg, find, cat."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

import click

from research._render import DEFAULT_SCOUT_MAX_CHARS, truncate_output
from research._source_ledger import record_visible_sources
from research.scout import cli
from research.scout._clone import current_head, ensure_ref, ensure_repo
from research.scout._common import github_url, parse_repo

# Map common file extension aliases to ripgrep type names.
# Only applied on the rg --type= path; git-grep uses raw extension globs.
_TYPE_ALIASES: dict[str, str] = {
    "tsx": "ts",
    "jsx": "js",
    "rs": "rust",
    "kt": "kotlin",
    "cs": "csharp",
}


def _partition_paths(
    repo_dir: Path,
    paths: tuple[str, ...],
    ref: str | None = None,
) -> tuple[list[str], list[str]]:
    """Return valid and missing repo-relative search paths."""
    valid: list[str] = []
    missing: list[str] = []
    for path in paths:
        if ref is None:
            exists = (repo_dir / path).exists()
        elif path == ".":
            exists = True
        else:
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{ref}:{path}"],
                capture_output=True,
                text=True,
                cwd=repo_dir,
                check=False,
            )
            exists = result.returncode == 0
        (valid if exists else missing).append(path)
    return valid, missing


def _report_missing_paths(valid: list[str], missing: list[str]) -> None:
    """Warn about omitted paths or fail when none of the requested paths exist."""
    if not missing:
        return
    message = ", ".join(missing)
    if valid:
        click.echo(f"warning: omitted missing paths: {message}", err=True)
        return
    click.echo(f"error: search paths not found: {message}", err=True)
    sys.exit(1)


@cli.command(name="rg")
@click.argument("repo")
@click.argument("pattern")
@click.option("--path", "paths", multiple=True, help="search path (repeatable; default: repo root)")
@click.option("--glob", "-g", "globs", multiple=True, help="file glob filter (repeatable)")
@click.option("--type", "filetypes", multiple=True, help="ripgrep type filter (repeatable)")
@click.option("--context", "-C", type=int, default=0, help="lines of context around matches")
@click.option("--ignore-case", "-i", is_flag=True, help="case-insensitive search")
@click.option("--fixed-strings", "-F", is_flag=True, help="treat pattern as literal string")
@click.option("--ref", help="branch, tag, or SHA (uses git grep)")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def rg_cmd(
    repo: str,
    pattern: str,
    paths: tuple[str, ...],
    globs: tuple[str, ...],
    filetypes: tuple[str, ...],
    context: int,
    ignore_case: bool,
    fixed_strings: bool,
    ref: str | None,
    max_chars: int,
) -> None:
    """Search cloned repo with ripgrep (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        source_ref = sha
        valid_paths, missing_paths = _partition_paths(repo_dir, paths, sha)
        _report_missing_paths(valid_paths, missing_paths)
        # git grep [opts] -e PATTERN REV [-- pathspec...]
        args = ["git", "grep", "--line-number", "--no-color"]
        if ignore_case:
            args.append("-i")
        if fixed_strings:
            args.append("--fixed-strings")
        if context > 0:
            args.append(f"-C{context}")
        args.extend(["-e", pattern, sha])
        # Pathspecs go after -- separator; use raw extension globs for git-grep
        pathspecs = valid_paths
        pathspecs.extend(globs)
        for ft in filetypes:
            pathspecs.append(f"*.{ft}")
        if pathspecs:
            args.append("--")
            args.extend(pathspecs)
        result = subprocess.run(args, capture_output=True, text=True, cwd=repo_dir, check=False)
    else:
        source_ref = current_head(repo_dir)
        valid_paths, missing_paths = _partition_paths(repo_dir, paths)
        _report_missing_paths(valid_paths, missing_paths)
        args = [
            "rg",
            "--line-number",
            "--no-heading",
            "--color=never",
            "--max-columns=200",
            "--max-columns-preview",
            "--no-follow",
        ]
        if ignore_case:
            args.append("--ignore-case")
        if fixed_strings:
            args.append("--fixed-strings")
        for ft in filetypes:
            mapped = _TYPE_ALIASES.get(ft, ft)
            args.append(f"--type={mapped}")
        for g in globs:
            args.extend(["--glob", g])
        if context > 0:
            args.extend(["-C", str(context)])
        args.append(pattern)
        args.extend(valid_paths or (".",))
        result = subprocess.run(args, capture_output=True, text=True, cwd=repo_dir, check=False)

    if result.returncode == 0:
        source = github_url(owner, name, "tree", source_ref)
        output = f"source: {source}\n\n{result.stdout}"
        rendered = truncate_output(
            output,
            max_chars,
            "narrow the pattern, --path, or file globs",
        )
        record_visible_sources(rendered, [source])
        click.echo(rendered, nl=False)
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
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def find_cmd(
    repo: str,
    pattern: str,
    limit: int,
    ref: str | None,
    max_chars: int,
) -> None:
    """Find files in cloned repo by glob pattern (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        source_ref = sha
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", sha],
            capture_output=True,
            text=True,
            cwd=repo_dir,
            check=False,
        )
        if result.returncode != 0:
            click.echo(f"error: git ls-tree failed: {result.stderr.strip()}", err=True)
            sys.exit(1)
        paths = [line for line in result.stdout.splitlines() if line]
        matches = sorted(
            p for p in paths if fnmatch.fnmatch(p, pattern) or fnmatch.fnmatch(p, f"*/{pattern}")
        )
    else:
        source_ref = current_head(repo_dir)
        matches = sorted(
            p.relative_to(repo_dir) for p in repo_dir.rglob(pattern) if ".git" not in p.parts
        )

    if not matches:
        click.echo("no matches")
        return
    total = len(matches)
    if limit > 0:
        matches = matches[:limit]
    source = github_url(owner, name, "tree", source_ref)
    output = f"source: {source}\n\n"
    output += "\n".join(str(match) for match in matches)
    if limit > 0 and total > limit:
        output += f"\n\n... {total - limit} more matches (increase --limit)"
    rendered = truncate_output(
        output,
        max_chars,
        "narrow the filename pattern or reduce --limit",
    )
    record_visible_sources(rendered, [source])
    click.echo(rendered)


@cli.command(name="cat")
@click.argument("repo")
@click.argument("path")
@click.option("--limit", "-L", type=int, default=240, help="max lines (0 = no limit)")
@click.option("--offset", type=int, default=0, help="skip first N lines")
@click.option("--ref", help="branch, tag, or SHA (uses git show)")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def cat_cmd(
    repo: str,
    path: str,
    limit: int,
    offset: int,
    ref: str | None,
    max_chars: int,
) -> None:
    """Read file from cloned repo (auto-clones on first use)."""
    owner, name = parse_repo(repo)
    repo_dir = ensure_repo(owner, name)

    if ref:
        sha = ensure_ref(owner, name, ref)
        source_ref = sha
        result = subprocess.run(
            ["git", "show", f"{sha}:{path}"],
            capture_output=True,
            text=True,
            cwd=repo_dir,
            check=False,
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
        source_ref = current_head(repo_dir)
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

    all_lines = content.split("\n")
    total = len(all_lines)
    lines = all_lines
    if offset:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]
    source = github_url(owner, name, "blob", source_ref, path)
    output = f"source: {source}\n\n" + "\n".join(lines)
    shown_through = offset + len(lines)
    if shown_through < total:
        output += (
            f"\n\n... {total - shown_through} more lines; continue with --offset {shown_through}"
        )
    rendered = truncate_output(
        output,
        max_chars,
        "reduce --limit, then continue with --offset",
    )
    record_visible_sources(rendered, [source])
    click.echo(rendered)
