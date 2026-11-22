"""Evaluation data directory, JSONL records, and URL identity."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlsplit

from research._search_results import url_key

__all__ = ["url_key"]

# Replayed queries come from private research sessions, so evaluation data stays outside the
# public repository.
DEFAULT_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "research-eval"

QUERIES = "queries.jsonl"
RESULTS_DIR = "results"
PAGES = "pages.jsonl"
JUDGMENTS = "judgments.jsonl"


def domain_matches(url: str, domains: list[str]) -> bool:
    """Return whether the URL's host is one of `domains` or a subdomain of one."""
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    for domain in domains:
        bare = domain.lower().removeprefix("www.").split("/")[0]
        if host == bare or host.endswith(f".{bare}"):
            return True
    return False


def read_jsonl(path: Path) -> Iterator[dict]:
    """Yield records from a JSONL file; a missing file yields nothing."""
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Replace the file with these records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, record: dict) -> None:
    """Append one record so interrupted runs keep finished work."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
