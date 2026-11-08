"""Microsoft Learn search through the official `mslearn` CLI (npm:@microsoft/learn-cli).

The CLI wraps Microsoft's Learn MCP server; shelling out keeps that protocol client maintained
upstream. Searches cost no Tavily credits and return one canonical (locale-free) URL per page.
Results carry no relevance score, so they are not score-filtered.
"""

from __future__ import annotations

import json
import subprocess

DOMAIN = "learn.microsoft.com"
_TIMEOUT_SECONDS = 30


class MsLearnError(Exception):
    """Microsoft Learn search failed."""


def search(query: str, max_results: int) -> list[dict]:
    """Return results shaped like Tavily's (`title`, `url`, `content`)."""
    try:
        result = subprocess.run(
            ["mslearn", "search", "--json", query],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        raise MsLearnError("search failed: mslearn CLI not found on PATH") from None
    except subprocess.TimeoutExpired:
        raise MsLearnError("search failed: timeout") from None
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
        raise MsLearnError(f"search failed: {detail}")
    try:
        items = json.loads(result.stdout)["results"]
        results = [
            {"title": item.get("title"), "url": item["contentUrl"], "content": item.get("content")}
            for item in items
            if item.get("contentUrl")
        ]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
        raise MsLearnError("search failed: unexpected mslearn output") from e
    return results[:max_results]
