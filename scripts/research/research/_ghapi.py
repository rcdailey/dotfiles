"""Private wrapper around `gh api` and `gh` subprocess calls."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from research._errors import die


def check_deps() -> None:
    """Verify gh CLI is available. Called once at startup."""
    if not shutil.which("gh"):
        die("gh not found; install the GitHub CLI first")


def _run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run gh CLI with given args, returning result."""
    try:
        return subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=check,
        )
    except FileNotFoundError:
        die("`gh` CLI not found in PATH")


def api(endpoint: str, method: str = "GET", params: dict[str, str] | None = None) -> dict | list:
    """Make a GitHub API call and return parsed JSON."""
    args = ["api", endpoint, "--method", method]
    if params:
        for key, value in params.items():
            args.extend(["-f", f"{key}={value}"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or f"gh api failed with exit {result.returncode}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON response: {e}") from e


def api_raw(endpoint: str, params: dict[str, str] | None = None) -> str:
    """Fetch an endpoint as raw content (e.g., file contents via Accept header)."""
    args = ["api", endpoint, "--method", "GET", "-H", "Accept: application/vnd.github.v3.raw"]
    if params:
        for key, value in params.items():
            args.extend(["-f", f"{key}={value}"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "gh api raw failed")
    return result.stdout


def graphql(query: str, **variables: str) -> dict:
    """Run a GraphQL query; variables are passed as gh -F key=value."""
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-F", f"{key}={value}"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "gh graphql failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON response: {e}") from e


def default_branch(owner: str, repo: str) -> str:
    """Return the repository's default branch name."""
    args = ["repo", "view", f"{owner}/{repo}", "--json", "defaultBranchRef"]
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "failed to resolve default branch")
    try:
        return json.loads(result.stdout)["defaultBranchRef"]["name"]
    except (json.JSONDecodeError, KeyError) as e:
        raise APIError(f"unexpected response resolving default branch: {e}") from e


def resolve_ref(owner: str, repo: str, ref: str | None) -> str:
    """Return `ref` if provided, else the repo's default branch."""
    return ref if ref else default_branch(owner, repo)


def repo_info(owner: str, repo: str) -> dict[str, Any]:
    """Get repository metadata."""
    return api(f"repos/{owner}/{repo}")


def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    search: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List issues in a repository."""
    args = ["issue", "list", "-R", f"{owner}/{repo}", "-s", state, "-L", str(limit)]
    if search:
        args.extend(["-S", search])
    args.extend(["--json", "number,title,state,createdAt,closedAt"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "failed to list issues")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def view_issue(owner: str, repo: str, number: int) -> dict:
    """Get detailed issue information including comments."""
    args = [
        "issue",
        "view",
        str(number),
        "-R",
        f"{owner}/{repo}",
        "-c",
        "--json",
        "title,state,body,comments,createdAt,number",
    ]
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or f"failed to view issue #{number}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def list_prs(
    owner: str,
    repo: str,
    state: str = "open",
    search: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List pull requests in a repository."""
    args = ["pr", "list", "-R", f"{owner}/{repo}", "-s", state, "-L", str(limit)]
    if search:
        args.extend(["-S", search])
    args.extend(["--json", "number,title,state,createdAt,mergedAt"])

    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "failed to list PRs")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def view_pr(owner: str, repo: str, number: int) -> dict:
    """Get detailed PR information including comments and reviews."""
    args = [
        "pr",
        "view",
        str(number),
        "-R",
        f"{owner}/{repo}",
        "-c",
        "--json",
        "title,state,body,comments,reviews,createdAt,number,mergedAt",
    ]
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or f"failed to view PR #{number}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def list_releases(owner: str, repo: str, limit: int = 30) -> list[dict]:
    """List releases in a repository."""
    args = [
        "release",
        "list",
        "-R",
        f"{owner}/{repo}",
        "-L",
        str(limit),
        "--json",
        "tagName,name,publishedAt,isDraft,isPrerelease",
    ]
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or "failed to list releases")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def view_release(owner: str, repo: str, tag: str) -> dict:
    """Get detailed release information."""
    args = [
        "release",
        "view",
        tag,
        "-R",
        f"{owner}/{repo}",
        "--json",
        "tagName,name,body,publishedAt,author",
    ]
    result = _run_gh(args, check=False)
    if result.returncode != 0:
        raise APIError(result.stderr.strip() or f"failed to view release {tag}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise APIError(f"invalid JSON: {e}") from e


def _parse_paginated(text: str) -> list:
    """Parse concatenated JSON arrays output by gh api --paginate."""
    decoder = json.JSONDecoder()
    items: list = []
    pos = 0
    text = text.strip()
    while pos < len(text):
        while pos < len(text) and text[pos] in " \n\r\t":
            pos += 1
        if pos >= len(text):
            break
        obj, pos = decoder.raw_decode(text, pos)
        if isinstance(obj, list):
            items.extend(obj)
    return items


def list_commits(
    owner: str,
    repo: str,
    since: str | None = None,
    until: str | None = None,
    path: str | None = None,
    author: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List commits in a repository.

    When limit > 100, uses gh --paginate (GitHub REST caps per_page at 100)
    and truncates the result to limit items.
    """
    params: dict[str, str] = {}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    if path:
        params["path"] = path
    if author:
        params["author"] = author

    endpoint = f"repos/{owner}/{repo}/commits"

    if limit > 100:
        params["per_page"] = "100"
        query = "&".join(f"{k}={v}" for k, v in params.items())
        ep = f"{endpoint}?{query}" if query else endpoint
        result = _run_gh(["api", "--paginate", ep], check=False)
        if result.returncode != 0:
            raise APIError(result.stderr.strip() or "failed to list commits")
        try:
            data = _parse_paginated(result.stdout)
        except (json.JSONDecodeError, ValueError) as e:
            raise APIError(f"invalid JSON: {e}") from e
        if not isinstance(data, list):
            raise APIError("unexpected response type from commits API")
        return data[:limit]

    params["per_page"] = str(limit)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    ep = f"{endpoint}?{query}" if query else endpoint
    data = api(ep)
    if not isinstance(data, list):
        raise APIError("unexpected response type from commits API")
    return data


def view_commit(owner: str, repo: str, sha: str) -> dict:
    """Get detailed commit information."""
    return api(f"repos/{owner}/{repo}/commits/{sha}")


def file_history(owner: str, repo: str, path: str, limit: int = 30) -> list[dict]:
    """Get commit history for a specific file."""
    return list_commits(owner, repo, path=path, limit=limit)


def list_discussions(
    owner: str,
    repo: str,
    search: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List discussions in a repository via GraphQL."""
    query = """\
query($owner:String!,$repo:String!,$limit:Int!) {
  repository(owner:$owner,name:$repo) {
    discussions(first:$limit,orderBy:{field:CREATED_AT,direction:DESC}) {
      nodes { number title createdAt author { login } category { name } }
    }
  }
}"""
    try:
        data = graphql(query, owner=owner, repo=repo, limit=str(limit))
    except APIError as e:
        raise APIError(f"failed to list discussions: {e}") from e

    nodes = data.get("data", {}).get("repository", {}).get("discussions", {}).get("nodes", [])
    if search:
        needle = search.lower()
        nodes = [n for n in nodes if needle in n.get("title", "").lower()]
    return nodes


def view_discussion(owner: str, repo: str, number: int) -> dict:
    """Get discussion details including comments via GraphQL."""
    query = """\
query($owner:String!,$repo:String!,$number:Int!) {
  repository(owner:$owner,name:$repo) {
    discussion(number:$number) {
      number title body createdAt
      author { login }
      category { name }
      comments(first:50) {
        nodes { body createdAt author { login } }
      }
    }
  }
}"""
    try:
        data = graphql(query, owner=owner, repo=repo, number=str(number))
    except APIError as e:
        raise APIError(f"failed to view discussion #{number}: {e}") from e

    disc = data.get("data", {}).get("repository", {}).get("discussion")
    if not disc:
        raise APIError(f"discussion #{number} not found in {owner}/{repo}")
    disc["comments"] = disc.get("comments", {}).get("nodes", [])
    return disc


class APIError(Exception):
    """GitHub API call failed."""

    pass
