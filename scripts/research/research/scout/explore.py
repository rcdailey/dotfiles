"""Repo exploration: orient, diff."""

from __future__ import annotations

import re
from collections import Counter

import click

from research._ghapi import APIError, api, api_raw
from research.scout import cli
from research.scout._common import die, parse_repo

ORIENT_MAX_FILES = 8
ORIENT_MAX_FILE_LINES = 150
ORIENT_MAX_README_LINES = 200

KEY_FILE_PATTERNS = [
    re.compile(r"^README(\.md|\.rst|\.txt)?$"),
    re.compile(r"^package\.json$"),
    re.compile(r"^Cargo\.toml$"),
    re.compile(r"^go\.mod$"),
    re.compile(r"^pyproject\.toml$"),
    re.compile(r"^pom\.xml$"),
    re.compile(r"^build\.gradle(\.kts)?$"),
    re.compile(r"^composer\.json$"),
    re.compile(r"^Gemfile$"),
    re.compile(r"^mix\.exs$"),
    re.compile(r"^deno\.jsonc?$"),
    re.compile(r"^Makefile$"),
    re.compile(r"^Dockerfile$"),
    re.compile(r"^docker-compose\.ya?ml$"),
]


def _render_orient(owner: str, repo: str, ref: str | None, brief: bool) -> None:
    try:
        meta = api(f"repos/{owner}/{repo}")
    except APIError as e:
        die(f"failed to fetch repo metadata: {e}")
    resolved = ref or meta.get("default_branch") or "HEAD"

    click.echo("=== METADATA ===")
    for label, value in [
        ("name", meta.get("name", "?")),
        ("description", meta.get("description") or "none"),
        ("default branch", meta.get("default_branch", "?")),
        ("stars", meta.get("stargazers_count", 0)),
        ("forks", meta.get("forks_count", 0)),
        ("language", meta.get("language") or "none"),
        ("homepage", meta.get("homepage") or "none"),
        ("private", str(meta.get("private", False)).lower()),
        ("disk usage", f"{meta.get('size', 0)} KB"),
        ("ref", resolved),
    ]:
        click.echo(f"{label}: {value}")

    try:
        tree_data = api(f"repos/{owner}/{repo}/git/trees/{resolved}", params={"recursive": "1"})
    except APIError as e:
        die(f"failed to fetch tree: {e}")

    blob_paths = [item["path"] for item in tree_data.get("tree", []) if item["type"] == "blob"]
    truncated = tree_data.get("truncated", False)
    click.echo("")
    click.echo(f"=== STRUCTURE ({len(blob_paths)} files{', truncated' if truncated else ''}) ===")

    buckets: dict[str, list[str | None]] = {}
    for path in blob_paths:
        parts = path.split("/")
        if len(parts) == 1:
            bucket = "./"
        elif len(parts) == 2:
            bucket = f"{parts[0]}/"
        else:
            bucket = f"{parts[0]}/{parts[1]}/"
        filename = parts[-1]
        ext = f".{filename.rsplit('.', 1)[1]}" if "." in filename else None
        buckets.setdefault(bucket, []).append(ext)

    rows: list[tuple[str, int, str]] = []
    for bucket in sorted(buckets):
        extensions = buckets[bucket]
        counts = Counter(e for e in extensions if e)
        rows.append((bucket, len(extensions), " ".join(e for e, _ in counts.most_common(5))))

    if rows:
        col1 = max(len(r[0]) for r in rows[:100])
        col2 = max(len(f"{r[1]} files") for r in rows[:100])
        for directory, count, exts in rows[:100]:
            click.echo(f"{directory:<{col1}}  {f'{count} files':<{col2}}  {exts}")

    readme_path = next((p for p in blob_paths if KEY_FILE_PATTERNS[0].match(p)), None)
    if readme_path:
        try:
            content = api_raw(
                f"repos/{owner}/{repo}/contents/{readme_path}",
                params={"ref": resolved},
            )
            lines = content.splitlines()
            click.echo(f"\n=== FILE: {readme_path} ===")
            click.echo("\n".join(lines[:ORIENT_MAX_README_LINES]))
            remaining = len(lines) - ORIENT_MAX_README_LINES
            if remaining > 0:
                click.echo(f"... plus {remaining} more lines")
        except APIError:
            pass

    if brief:
        return

    shown = 0
    for pattern in KEY_FILE_PATTERNS:
        if shown >= ORIENT_MAX_FILES:
            break
        match_path = next((p for p in blob_paths if pattern.match(p)), None)
        if not match_path or match_path == readme_path:
            continue
        try:
            content = api_raw(
                f"repos/{owner}/{repo}/contents/{match_path}",
                params={"ref": resolved},
            )
        except APIError:
            continue
        click.echo(f"\n=== FILE: {match_path} ===")
        click.echo("\n".join(content.splitlines()[:ORIENT_MAX_FILE_LINES]))
        shown += 1


@cli.command()
@click.argument("repo")
@click.option("--brief", is_flag=True, help="skip key file contents")
@click.option("--ref", help="branch, tag, or SHA (default: repo's default branch)")
def orient(repo: str, brief: bool, ref: str | None) -> None:
    """Overview: metadata, structure summary, key files."""
    owner, name = parse_repo(repo)
    _render_orient(owner, name, ref, brief)


@cli.command(name="diff")
@click.argument("repo")
@click.argument("spec")
@click.option("--path", help="filter files by path prefix")
def diff_cmd(repo: str, spec: str, path: str | None) -> None:
    """Compare two refs: `scout diff REPO base..head`."""
    if ".." not in spec:
        raise click.UsageError("spec must be BASE..HEAD (e.g., v1.0..v2.0)")
    base, head = spec.split("..", 1)
    if not base or not head:
        raise click.UsageError("spec must be BASE..HEAD (e.g., v1.0..v2.0)")

    owner, name = parse_repo(repo)
    try:
        data = api(f"repos/{owner}/{name}/compare/{base}...{head}")
    except APIError as e:
        die(str(e))

    click.echo(
        f"ahead: {data['ahead_by']}, behind: {data['behind_by']}, "
        f"total commits: {data['total_commits']}"
    )
    commits_list = data.get("commits", [])
    files = data.get("files", [])
    if path:
        files = [f for f in files if f["filename"].startswith(path)]

    if commits_list:
        click.echo("\n=== COMMITS ===")
        for c in commits_list:
            sha = c["sha"][:8]
            msg = c["commit"]["message"].split("\n", 1)[0]
            click.echo(f"{sha} {msg[:120]}")
    if files:
        click.echo("\n=== FILES ===")
        for f in files:
            click.echo(f"{f['status']:<12} +{f['additions']}-{f['deletions']} {f['filename']}")
