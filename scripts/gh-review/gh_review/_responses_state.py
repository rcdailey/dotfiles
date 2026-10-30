"""Last-checked times for `responses`, kept in a secret gist so every machine shares them.

The gist holds one JSON file mapping a scope key (see `scope_key`) to the ISO-8601 time up to
which replies and reactions were already reported. The gist is found by its description and
created on the first write.
"""

from __future__ import annotations

import json

from gh_review._gh import gh_rest_json, gh_rest_pages

GIST_DESCRIPTION = "gh-review responses state"
GIST_FILE = "gh-review-responses.json"


def scope_key(org: str | None, exclude_org: str | None) -> str:
    """Name the org filter so each filter keeps its own last-checked time."""
    if org:
        return f"only:{org.lower()}"
    if exclude_org:
        return f"not:{exclude_org.lower()}"
    return "all"


def _find_gist() -> dict | None:
    return next(
        (g for g in gh_rest_pages("gists") if g.get("description") == GIST_DESCRIPTION),
        None,
    )


def _read(gist_id: str) -> dict[str, str]:
    files = gh_rest_json("GET", f"gists/{gist_id}")["files"]
    entry = files.get(GIST_FILE)
    return json.loads(entry["content"]) if entry and entry.get("content") else {}


def load_checked(scope: str) -> str | None:
    """Return the last-checked time for a scope, or None if it was never acknowledged."""
    gist = _find_gist()
    return _read(gist["id"]).get(scope) if gist else None


def save_checked(scope: str, checked: str) -> None:
    """Record the last-checked time for a scope, creating the gist when missing."""
    gist = _find_gist()
    state = _read(gist["id"]) if gist else {}
    state[scope] = checked
    files = {GIST_FILE: {"content": json.dumps(state, indent=2, sort_keys=True) + "\n"}}
    if gist:
        gh_rest_json("PATCH", f"gists/{gist['id']}", {"files": files})
        return
    gh_rest_json(
        "POST", "gists", {"description": GIST_DESCRIPTION, "public": False, "files": files}
    )
