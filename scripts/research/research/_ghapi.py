"""Private wrapper around `gh api` and `gh` subprocess calls."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any


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
        print("error: `gh` CLI not found in PATH", file=sys.stderr)
        sys.exit(2)


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
    args.extend(["--json", "number,title,state,createdAt"])

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


def list_commits(
    owner: str,
    repo: str,
    since: str | None = None,
    until: str | None = None,
    path: str | None = None,
    author: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List commits in a repository."""
    params: dict[str, str] = {"per_page": str(limit)}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    if path:
        params["path"] = path
    if author:
        params["author"] = author

    endpoint = f"repos/{owner}/{repo}/commits"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        endpoint += f"?{query}"

    data = api(endpoint)
    if not isinstance(data, list):
        raise APIError("unexpected response type from commits API")
    return data


def view_commit(owner: str, repo: str, sha: str) -> dict:
    """Get detailed commit information."""
    return api(f"repos/{owner}/{repo}/commits/{sha}")


def file_history(owner: str, repo: str, path: str, limit: int = 30) -> list[dict]:
    """Get commit history for a specific file."""
    return list_commits(owner, repo, path=path, limit=limit)


class APIError(Exception):
    """GitHub API call failed."""

    pass
