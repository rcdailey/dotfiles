"""Repo exploration: orient, tree, read, blame, diff, code."""

from __future__ import annotations

import base64
import re
import textwrap
import urllib.error
import urllib.request
from collections import Counter

import click

from research._budget import budget_reserve
from research._cache import get_cache
from research._ghapi import APIError, _run_gh, api, api_raw, graphql, resolve_ref
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

_REGEX_META_RE = re.compile(
    r"(?:(?<!\\)\||(?:\\[.dwsDWS])|(?:\.\*|\.\+)|(?:\\\(|\\\))|(?:\\\[|\\\]))"
)


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
    budget_reserve(get_cache(), None)
    _render_orient(owner, name, ref, brief)


@cli.command()
@click.argument("repo")
@click.argument("path", required=False, default="")
@click.option(
    "--depth",
    type=int,
    default=0,
    help="max directory depth; 1 = flat listing, 0 = full recursive (default)",
)
@click.option("--ref", help="branch, tag, or SHA")
@click.option("--limit", type=int, default=0, help="max entries (0 = no limit)")
def tree(repo: str, path: str, depth: int, ref: str | None, limit: int) -> None:
    """List directory contents (--depth 1) or full recursive tree."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)

    if depth == 1:
        params: dict[str, str] = {}
        if ref:
            params["ref"] = ref
        try:
            data = api(f"repos/{owner}/{name}/contents/{path}", params=params)
        except APIError as e:
            die(str(e))
        items = data if isinstance(data, list) else [data]
        items = sorted(items, key=lambda x: (x["type"] != "dir", x["name"]))
        if limit:
            items = items[:limit]
        for item in items:
            suffix = "/" if item["type"] == "dir" else f"  {item['size']}B"
            click.echo(f"{item['name']}{suffix}")
        return

    resolved = resolve_ref(owner, name, ref)
    try:
        data = api(f"repos/{owner}/{name}/git/trees/{resolved}", params={"recursive": "1"})
    except APIError as e:
        die(str(e))

    paths = [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]
    if path:
        prefix = path.rstrip("/") + "/"
        paths = [p for p in paths if p.startswith(prefix)]
    if depth > 1:
        paths = [p for p in paths if p.count("/") < depth]
    if limit:
        paths = paths[:limit]
    for p in paths:
        click.echo(p)


@cli.command()
@click.argument("repo")
@click.argument("path")
@click.option("--ref", default="HEAD", help="branch, tag, or SHA")
@click.option("--limit", type=int, default=0, help="max lines (0 = no limit)")
@click.option("--offset", type=int, default=0, help="skip first N lines")
def read(repo: str, path: str, ref: str, limit: int, offset: int) -> None:
    """Read file contents (raw, no envelope)."""
    owner, name = parse_repo(repo)
    raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/{ref}/{path}"
    budget_reserve(get_cache(), raw_url)

    try:
        with urllib.request.urlopen(raw_url, timeout=30) as response:
            content = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            die(f"HTTP {e.code} fetching file")
        try:
            data = api(f"repos/{owner}/{name}/contents/{path}", params={"ref": ref})
        except APIError as api_err:
            die(f"failed to read file: {api_err}")
        if not isinstance(data, dict) or "content" not in data:
            die("unexpected response from GitHub API")
        content = base64.b64decode(data["content"]).decode("utf-8")

    lines = content.split("\n")
    if offset:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]
    click.echo("\n".join(lines))


@cli.command()
@click.argument("repo")
@click.argument("path")
@click.option("--ref", help="branch, tag, or SHA")
def blame(repo: str, path: str, ref: str | None) -> None:
    """Line-by-line attribution."""
    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)
    resolved = resolve_ref(owner, name, ref)
    query = textwrap.dedent("""\
        query($owner:String!,$repo:String!,$ref:String!,$path:String!) {
          repository(owner:$owner,name:$repo) {
            object(expression:$ref) {
              ... on Commit {
                blame(path:$path) { ranges {
                  startingLine endingLine
                  commit {
                    abbreviatedOid message
                    author { name date }
                  }
                }}
              }
            }
          }
        }""")
    try:
        result = graphql(query, owner=owner, repo=name, ref=resolved, path=path)
    except APIError as e:
        die(str(e))

    try:
        ranges = result["data"]["repository"]["object"]["blame"]["ranges"]
    except (KeyError, TypeError):
        die("no blame data; verify repo, path, and ref")

    for r in ranges:
        c = r["commit"]
        msg = c["message"].split("\n", 1)[0]
        click.echo(
            f"L{r['startingLine']}-{r['endingLine']} "
            f"{c['abbreviatedOid']} {c['author']['name']} "
            f"({c['author']['date']}): {msg}"
        )


@cli.command(name="diff")
@click.argument("repo")
@click.argument("spec")
@click.option("--path", help="filter files by path prefix")
def diff_cmd(repo: str, spec: str, path: str | None) -> None:
    """Compare two refs: `scout diff REPO base..head`."""
    if ".." not in spec:
        die("spec must be BASE..HEAD (e.g., v1.0..v2.0)", code=2)
    base, head = spec.split("..", 1)
    if not base or not head:
        die("spec must be BASE..HEAD (e.g., v1.0..v2.0)", code=2)

    owner, name = parse_repo(repo)
    budget_reserve(get_cache(), None)
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


@cli.command(name="code")
@click.argument("query")
@click.option(
    "--in", "scopes", multiple=True, metavar="OWNER/REPO", help="scope to repo; repeatable"
)
@click.option("--limit", type=int, default=20)
def code_cmd(query: str, scopes: tuple[str, ...], limit: int) -> None:
    """Search code across GitHub (no regex; `|` is literal)."""
    import json

    if _REGEX_META_RE.search(query):
        die(
            'GitHub code search is literal, not regex; "|" is treated as a character. '
            "Run separate searches for each term.",
            code=2,
        )
    budget_reserve(get_cache(), None)

    args = [
        "search",
        "code",
        query,
        "--limit",
        str(limit),
        "--json",
        "path,repository,textMatches",
    ]
    for s in scopes:
        args.extend(["--repo", s])
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        die(result.stderr.strip() or "code search failed")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        die(f"invalid JSON from gh search: {e}")

    if not data:
        click.echo("no results")
        return

    scoped = len(scopes) == 1
    for i, item in enumerate(data):
        slug = item["repository"]["nameWithOwner"]
        header = item["path"] if scoped else f"{slug}:{item['path']}"
        if i > 0:
            click.echo("")
        click.echo(header)
        for j, match in enumerate(item.get("textMatches", [])):
            if j > 0:
                click.echo("---")
            for line in match["fragment"].splitlines():
                click.echo(f"| {line}")
