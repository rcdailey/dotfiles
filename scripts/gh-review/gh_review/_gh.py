"""Low-level helpers for calling the GitHub CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any

from gh_review._errors import GhError, die


def check_deps() -> None:
    """Verify gh CLI is installed and authenticated."""
    if not shutil.which("gh"):
        die("gh CLI not found")
    result = subprocess.run(["gh", "auth", "status"], capture_output=True)
    if result.returncode != 0:
        die("gh not authenticated; run 'gh auth login'")


def _parse_status(stderr: str) -> int:
    """Extract HTTP status code from gh CLI stderr, e.g. '(HTTP 404)'."""
    m = re.search(r"\(HTTP (\d+)\)", stderr)
    return int(m.group(1)) if m else 0


def run_gh(*args: str) -> str:
    """Run gh with args, return stdout. Raises GhError on failure."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise GhError(result.stderr.strip(), status=_parse_status(result.stderr))
    return result.stdout


def gh_graphql(query: str, **variables: str) -> Any:
    """Execute a GraphQL query via gh CLI."""
    cmd = ["api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        cmd.extend(["-F", f"{k}={v}"])
    return json.loads(run_gh(*cmd))


def gh_graphql_mutation(query: str, variables: dict[str, Any]) -> Any:
    """Execute a GraphQL mutation with full variable support (nested objects)."""
    payload = json.dumps({"query": query, "variables": variables})
    result = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=payload,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GhError(result.stderr.strip())
    data = json.loads(result.stdout)
    if "errors" in data:
        msgs = "; ".join(e.get("message", str(e)) for e in data["errors"])
        raise GhError(msgs)
    return data


def gh_rest(
    method: str,
    endpoint: str,
    body: dict[str, Any] | None = None,
    jq: str | None = None,
) -> str:
    """Execute a GitHub REST API call via gh CLI."""
    cmd = ["api", "--method", method, endpoint]
    if body:
        for k, v in body.items():
            cmd.extend(["-f", f"{k}={v}"])
    if jq:
        cmd.extend(["--jq", jq])
    return run_gh(*cmd)


def split_repo(repo: str) -> tuple[str, str]:
    """Split 'owner/name' into (owner, name). Dies on invalid format."""
    if "/" not in repo:
        die(f"invalid repo format: {repo} (expected owner/name)")
    owner, name = repo.split("/", 1)
    return owner, name
