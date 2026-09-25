"""Fork discovery: find forks whose own commits match a pattern or path."""

from __future__ import annotations

import json
import re
import sys

import click

from research._ghapi import APIError, graphql_partial, view_commit
from research._render import DEFAULT_SCOUT_MAX_CHARS, format_commit_item, truncate_output
from research._source_ledger import record_visible_sources
from research.scout import cli
from research.scout._common import die, github_url, more_results_hint, parse_repo

# Rate-limit posture: each GraphQL request lists _PAGE_SIZE forks, lists branches of _BATCH forks,
# or compares _BATCH branches, and costs about one of the 5000 hourly GraphQL points; a default
# run costs about 20 points. --diff adds at most _MAX_DIFF_FETCHES REST calls. Requests run
# sequentially and stop at the first failure so a limited session is not retried into a
# secondary rate limit.
_PAGE_SIZE = 50
_MAX_PAGES = 10
_MAX_SCAN = 100
_BATCH = 10
_BRANCH_PAGE = 100
_BRANCHES_PER_FORK = 3
_COMMITS_PER_BRANCH = 50
_SHOWN_PER_BRANCH = 10
_UNFILTERED_PREVIEW = 5
_MAX_DIFF_FETCHES = 30
_URL = re.compile(r"https://github\.com/\S+")


def _gql(value: str) -> str:
    return json.dumps(value)


def _fork_page(owner: str, name: str, order: str, cursor: str | None) -> dict:
    after = f", after: {_gql(cursor)}" if cursor else ""
    query = f"""query {{
  repository(owner: {_gql(owner)}, name: {_gql(name)}) {{
    forkCount
    defaultBranchRef {{ name }}
    forks(first: {_PAGE_SIZE}{after}, orderBy: {{field: {order}, direction: DESC}}) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{
        name owner {{ login }} stargazerCount pushedAt createdAt isArchived
        defaultBranchRef {{ name }}
      }}
    }}
  }}
}}"""
    data, errors = graphql_partial(query)
    repo = data.get("repository")
    if not repo:
        raise APIError("; ".join(e.get("message", "?") for e in errors) or "repository not found")
    return repo


def _list_candidates(owner: str, name: str, order: str, scan: int) -> tuple[dict, int, list]:
    """Page through forks until `scan` forks with own pushes are found.

    Returns upstream metadata, the number of forks listed, and the candidates.
    """
    cursor = None
    listed = 0
    candidates: list[dict] = []
    for _ in range(_MAX_PAGES):
        repo = _fork_page(owner, name, order, cursor)
        page = repo["forks"]
        listed += len(page["nodes"])
        candidates.extend(fork for fork in page["nodes"] if _has_own_pushes(fork))
        if len(candidates) >= scan or not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return repo, listed, candidates[:scan]


def _has_own_pushes(fork: dict) -> bool:
    """A fork created without later pushes keeps the parent's older pushedAt."""
    return bool(fork.get("defaultBranchRef")) and fork["pushedAt"] > fork["createdAt"]


def _compile(value: str | None, option: str) -> re.Pattern[str] | None:
    try:
        return re.compile(value, re.IGNORECASE) if value else None
    except re.error as e:
        raise click.BadParameter(f"invalid regex: {e}", param_hint=option) from e


def _slug(fork: dict) -> str:
    return f"{fork['owner']['login']}/{fork['name']}"


def _repo_field(alias: str, fork: dict, body: str) -> str:
    owner, name = _gql(fork["owner"]["login"]), _gql(fork["name"])
    return f"{alias}: repository(owner: {owner}, name: {name}) {{ {body} }}"


def _field_failures(errors: list[dict], labels: dict[str, str]) -> list[str]:
    """Name the fork or branch behind each failed aliased field."""
    failures = []
    for error in errors:
        message = error.get("message", "?")
        label = next((labels[p] for p in error.get("path", []) if p in labels), None)
        failures.append(f"{label} unavailable: {message}" if label else message)
    return failures


def _branch_targets(forks: list[dict]) -> tuple[list[dict], list[str], dict | None]:
    """Pick each fork's newest branches whose tips postdate the fork.

    Older tips are treated as branches copied from upstream at fork time. GraphQL cannot order
    branches by commit date, so only the first _BRANCH_PAGE branches are considered.
    """
    fields = [
        _repo_field(
            f"r{i}",
            fork,
            f'refs(refPrefix: "refs/heads/", first: {_BRANCH_PAGE}) '
            "{ nodes { name target { ... on Commit { committedDate } } } }",
        )
        for i, fork in enumerate(forks)
    ]
    data, errors = graphql_partial(
        f"query {{ rateLimit {{ remaining resetAt }} {' '.join(fields)} }}"
    )
    labels = {f"r{i}": f"{_slug(fork)} branches" for i, fork in enumerate(forks)}
    targets = []
    for i, fork in enumerate(forks):
        nodes = ((data.get(f"r{i}") or {}).get("refs") or {}).get("nodes", [])
        tips = [
            (date, node["name"])
            for node in nodes
            if (date := (node.get("target") or {}).get("committedDate", "")) > fork["createdAt"]
        ]
        targets.extend(
            {"fork": fork, "branch": branch}
            for _, branch in sorted(tips, reverse=True)[:_BRANCHES_PER_FORK]
        )
    return targets, _field_failures(errors, labels), data.get("rateLimit")


def _compare_targets(
    owner: str, name: str, targets: list[dict], path: str | None
) -> tuple[dict, list[str]]:
    compares = []
    histories = []
    labels = {}
    for k, target in enumerate(targets):
        fork, branch = target["fork"], target["branch"]
        head = f"{fork['owner']['login']}:{fork['name']}:{branch}"
        labels[f"c{k}"] = f"{_slug(fork)}@{branch} compare"
        compares.append(
            f"c{k}: compare(headRef: {_gql(head)}) {{ aheadBy behindBy "
            f"commits(last: {_COMMITS_PER_BRANCH}) {{ nodes {{ oid message committedDate "
            f"parents {{ totalCount }} }} }} }}"
        )
        if path:
            labels[f"h{k}"] = f"{_slug(fork)}@{branch} path history"
            histories.append(
                _repo_field(
                    f"h{k}",
                    fork,
                    f"ref(qualifiedName: {_gql(f'refs/heads/{branch}')}) {{ target {{ "
                    f"... on Commit {{ history(first: {_COMMITS_PER_BRANCH}, "
                    f"path: {_gql(path)}) {{ nodes {{ oid }} }} }} }} }}",
                )
            )
    query = (
        "query { rateLimit { remaining resetAt } "
        f"upstream: repository(owner: {_gql(owner)}, name: {_gql(name)}) "
        f"{{ defaultBranchRef {{ {' '.join(compares)} }} }} {' '.join(histories)} }}"
    )
    data, errors = graphql_partial(query)
    return data, _field_failures(errors, labels)


def _path_oids(data: dict, index: int) -> set[str]:
    repo = data.get(f"h{index}") or {}
    target = (repo.get("ref") or {}).get("target") or {}
    return {node["oid"] for node in (target.get("history") or {}).get("nodes", [])}


def _diff_match(fork: dict, oid: str, pattern: re.Pattern[str], path: str | None) -> str | None:
    """Return the first file whose added or removed lines match, if any."""
    data = view_commit(fork["owner"]["login"], fork["name"], oid)
    for file in data.get("files", []):
        if path and not file.get("filename", "").startswith(path):
            continue
        for line in (file.get("patch") or "").splitlines():
            if line.startswith(("+", "-")) and pattern.search(line[1:]):
                return file["filename"]
    return None


def _render_fork(owner: str, name: str, base: str, fork: dict, branches: list[dict]) -> str:
    login, fork_name = fork["owner"]["login"], fork["name"]
    lines = [
        f"=== {login}/{fork_name} ===",
        f"stars: {fork['stargazerCount']}, last push: {fork['pushedAt'][:10]}"
        + (", archived" if fork["isArchived"] else ""),
        f"source: {github_url(login, fork_name)}",
    ]
    for entry in branches:
        compare, commits = entry["compare"], entry["commits"]
        head = f"{login}:{fork_name}:{entry['branch']}"
        ahead = compare["aheadBy"]
        checked = f" (newest {_COMMITS_PER_BRANCH} checked)" if ahead > _COMMITS_PER_BRANCH else ""
        lines.append(
            f"branch {entry['branch']}: ahead {ahead}{checked}, behind {compare['behindBy']}"
        )
        lines.append(f"compare: {github_url(owner, name, 'compare', f'{base}...{head}')}")
        if len(commits) > _SHOWN_PER_BRANCH:
            lines.append(f"matching commits: {len(commits)}, newest {_SHOWN_PER_BRANCH} shown")
        for commit in commits[:_SHOWN_PER_BRANCH]:
            lines.append(
                format_commit_item(
                    commit["oid"],
                    commit["committedDate"],
                    commit["message"].split("\n", 1)[0],
                    source_url=github_url(login, fork_name, "commit", commit["oid"]),
                )
            )
            if commit.get("diff_file"):
                lines.append(f"  diff match: {commit['diff_file']}")
    return "\n".join(lines)


@cli.command()
@click.argument("repo")
@click.option("--grep", help="case-insensitive regex matched against fork commit messages")
@click.option("--path", help="keep fork commits that touch this file or directory")
@click.option(
    "--diff",
    help="case-insensitive regex matched against changed lines of commits kept by --grep/--path",
)
@click.option(
    "--sort",
    type=click.Choice(["pushed", "stars"]),
    default="pushed",
    help="order used to pick which forks to scan",
)
@click.option(
    "--scan",
    type=click.IntRange(min=1, max=_MAX_SCAN),
    default=40,
    help="max forks with own pushes to compare",
)
@click.option("--limit", "-L", type=click.IntRange(min=1), default=10, help="max forks shown")
@click.option(
    "--max-chars",
    type=click.IntRange(min=1, max=DEFAULT_SCOUT_MAX_CHARS),
    default=DEFAULT_SCOUT_MAX_CHARS,
)
def forks(
    repo: str,
    grep: str | None,
    path: str | None,
    diff: str | None,
    sort: str,
    scan: int,
    limit: int,
    max_chars: int,
) -> None:
    """Find forks with own commits, optionally matching --grep, --path, and --diff.

    Compares each direct fork's 3 most recently committed branches with upstream's default
    branch and skips merge commits. Forks without pushes after creation are skipped without a
    compare; listing stops after 500 forks.
    """
    pattern = _compile(grep, "--grep")
    diff_pattern = _compile(diff, "--diff")
    if diff and not (grep or path):
        raise click.UsageError("--diff requires --grep or --path to bound commit fetches")
    owner, name = parse_repo(repo)

    order = "PUSHED_AT" if sort == "pushed" else "STARGAZERS"
    try:
        upstream, listed, candidates = _list_candidates(owner, name, order, scan)
    except APIError as e:
        die(str(e))
    if not upstream.get("defaultBranchRef"):
        die(f"{repo} has no default branch to compare against")
    base = upstream["defaultBranchRef"]["name"]

    matched: list[str] = []
    failures: list[str] = []
    scanned = 0
    rate = None
    diff_fetches = 0
    diff_skipped = 0

    def diff_filter(fork: dict, commits: list[dict]) -> list[dict]:
        nonlocal diff_fetches, diff_skipped
        kept = []
        for commit in commits:
            if diff_fetches >= _MAX_DIFF_FETCHES:
                diff_skipped += 1
                continue
            diff_fetches += 1
            try:
                file = _diff_match(fork, commit["oid"], diff_pattern, path)
            except APIError as e:
                failures.append(f"{_slug(fork)} commit {commit['oid'][:8]} unavailable: {e}")
                continue
            if file:
                kept.append({**commit, "diff_file": file})
        return kept

    for start in range(0, len(candidates), _BATCH):
        batch = candidates[start : start + _BATCH]
        try:
            targets, errors, rate = _branch_targets(batch)
            failures.extend(errors)
            compared: list[tuple[dict, dict, set[str]]] = []
            for chunk_start in range(0, len(targets), _BATCH):
                chunk = targets[chunk_start : chunk_start + _BATCH]
                data, errors = _compare_targets(owner, name, chunk, path)
                failures.extend(errors)
                rate = data.get("rateLimit") or rate
                branch_data = (data.get("upstream") or {}).get("defaultBranchRef") or {}
                compared.extend(
                    (target, branch_data[f"c{k}"], _path_oids(data, k))
                    for k, target in enumerate(chunk)
                    if branch_data.get(f"c{k}")
                )
        except APIError as e:
            failures.append(f"stopped after {scanned} forks: {e}")
            break
        scanned += len(batch)

        for fork in batch:
            seen: set[str] = set()
            branches = []
            for target, compare, touched in compared:
                if target["fork"] is not fork or compare["aheadBy"] == 0:
                    continue
                commits = [
                    c
                    for c in reversed(compare["commits"]["nodes"])
                    if c["parents"]["totalCount"] < 2 and c["oid"] not in seen
                ]
                seen.update(c["oid"] for c in commits)
                if pattern:
                    commits = [c for c in commits if pattern.search(c["message"])]
                if path:
                    commits = [c for c in commits if c["oid"] in touched]
                if diff_pattern:
                    commits = diff_filter(fork, commits)
                if not (pattern or path):
                    commits = commits[:_UNFILTERED_PREVIEW]
                if commits:
                    branches.append(
                        {"branch": target["branch"], "compare": compare, "commits": commits}
                    )
            if branches:
                matched.append(_render_fork(owner, name, base, fork, branches))

    filters = ", ".join(
        part
        for part in (grep and f"grep: {grep}", path and f"path: {path}", diff and f"diff: {diff}")
        if part
    )
    summary = [
        f"## Forks of {repo}",
        (
            f"compared the newest {_BRANCHES_PER_FORK} branches of {scanned} forks with own "
            f"pushes among the first {listed} of {upstream['forkCount']} listed (sort: {sort}); "
            f"{len(matched)} with matching own commits" + (f" ({filters})" if filters else "")
        ),
        f"source: {github_url(owner, name, 'forks')}",
    ]
    if diff_skipped:
        summary.append(
            f"diff check capped at {_MAX_DIFF_FETCHES} commits; {diff_skipped} candidate "
            "commits unchecked; narrow --grep/--path or --scan"
        )
    if rate:
        summary.append(f"graphql points remaining: {rate['remaining']} (resets {rate['resetAt']})")
    shown = matched[:limit]
    output = "\n\n".join(["\n".join(summary), *shown])
    if len(matched) > limit:
        output += f"\n\n{more_results_hint(limit)}"
    if not matched:
        output += "\n\nNo forks matched."
    rendered = truncate_output(output, max_chars, "reduce --limit or narrow with --grep/--path")
    record_visible_sources(rendered, _URL.findall(rendered))
    click.echo(rendered)
    if failures:
        click.echo(f"error: forks incomplete: {'; '.join(failures)}", err=True)
        sys.exit(1)
