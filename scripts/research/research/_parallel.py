"""Parallel API client: web search, and page extraction when local fetching fails."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from curl_cffi import requests

from research._secrets import SecretError, read_secret

_BASE_URL = "https://api.parallel.ai/v1"
_TIMEOUT = 30
_EXTRACT_TIMEOUT = 90
_MAX_RETRY_WAIT = 10
# Fast mode matched advanced and basic on replayed researcher queries at a fifth of their price
# (docs/decisions/0003-parallel-fast-search.md).
MODE = "fast"
# Uncapped fast-mode excerpts run about 2,500 characters per result; 1,200 keeps a default
# 10-result search near 12,000 characters and shrinks smaller searches with it.
CHARS_PER_RESULT = 1200
_DAYS = {"day": 1, "week": 7, "month": 31, "year": 365}
_TOOL_ERROR = "report this as a tool error"


_RETRY_OR_GAP = "retry later or record the gap"


class ParallelError(Exception):
    """A Parallel request failed.

    `reason` says what happened and `advice` what the agent should do next; the message joins
    them. `page_missing` marks an extraction whose target page does not exist.
    """

    def __init__(self, reason: str, advice: str | None = None, page_missing: bool = False):
        super().__init__(f"{reason}; {advice}" if advice else reason)
        self.reason = reason
        self.advice = advice
        self.page_missing = page_missing


def _retry_wait(response: object) -> float:
    try:
        wait = float(response.headers.get("retry-after") or 2)
    except ValueError:
        wait = 2
    return min(wait, _MAX_RETRY_WAIT)


def _error_detail(response: object) -> str:
    """Return the API's own error message rather than raw JSON."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200].strip() or "no detail"
    error = body.get("error") if isinstance(body, dict) else None
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])[:300]
    if isinstance(body, dict) and body.get("detail"):
        return str(body["detail"])[:300]
    return str(body)[:200]


def _post(endpoint: str, body: dict, action: str, timeout: int = _TIMEOUT) -> dict:
    """POST to the API, retrying once after a rate limit, server error, or timeout."""
    try:
        key = read_secret("PARALLEL_API_KEY", "parallel-api-key")
    except SecretError as e:
        raise ParallelError(f"{action} failed: {e}", _TOOL_ERROR) from e
    for attempt in range(2):
        retry = attempt == 0
        try:
            response = requests.post(
                f"{_BASE_URL}/{endpoint}",
                json=body,
                headers={"x-api-key": key},
                timeout=timeout,
            )
        except requests.exceptions.Timeout as e:
            if retry:
                continue
            raise ParallelError(f"{action} failed: timed out twice", _RETRY_OR_GAP) from e
        except requests.RequestsError as e:
            raise ParallelError(f"{action} failed: network error ({e})", _RETRY_OR_GAP) from e
        status = response.status_code
        if (status == 429 or status >= 500) and retry:
            time.sleep(_retry_wait(response))
            continue
        if status == 429:
            raise ParallelError(
                f"{action} failed: rate limited after one retry",
                "wait before the next call or record the gap",
            )
        if status >= 500:
            raise ParallelError(
                f"{action} failed: Parallel server error (HTTP {status}) after one retry",
                _RETRY_OR_GAP,
            )
        if status in (401, 402, 403):
            raise ParallelError(
                f"{action} failed: HTTP {status}: {_error_detail(response)}", _TOOL_ERROR
            )
        if status >= 400:
            raise ParallelError(f"{action} failed: HTTP {status}: {_error_detail(response)}")
        try:
            data = response.json()
        except ValueError as e:
            raise ParallelError(f"{action} failed: unreadable response", _TOOL_ERROR) from e
        if not isinstance(data, dict):
            raise ParallelError(f"{action} failed: unexpected response", _TOOL_ERROR)
        return data
    raise ParallelError(f"{action} failed: retry exhausted")  # unreachable; satisfies typing


def search(
    query: str,
    max_results: int,
    domains: tuple[str, ...] = (),
    exclude_domains: tuple[str, ...] = (),
    time_range: str | None = None,
    mode: str = MODE,
) -> list[dict]:
    """Return ranked results shaped as `title`, `url`, `content`, `published`.

    The query is sent as both objective and keyword query, the configuration the evaluation
    measured. Results must match `domains` when set and never match `exclude_domains`, so an
    exclusion can carve a subdomain out of an included domain. Entries may be domains,
    domain/path prefixes, or suffixes such as `.gov`.
    """
    policy: dict = {}
    if domains:
        policy["include_domains"] = list(domains)
    if exclude_domains:
        policy["exclude_domains"] = list(exclude_domains)
    if time_range:
        since = datetime.now(UTC).date() - timedelta(days=_DAYS[time_range])
        policy["after_date"] = since.isoformat()
    settings: dict = {"max_results": max_results}
    if policy:
        settings["source_policy"] = policy
    body = {
        "objective": query,
        "search_queries": [query],
        "mode": mode,
        "max_chars_total": CHARS_PER_RESULT * max_results,
        "advanced_settings": settings,
    }
    data = _post("search", body, "search")
    try:
        return [
            {
                "title": r.get("title") or "",
                "url": r["url"],
                "content": "\n\n".join(r.get("excerpts") or []),
                "published": r.get("publish_date"),
            }
            for r in data.get("results") or []
        ]
    except (KeyError, TypeError, AttributeError) as e:
        raise ParallelError("search failed: unexpected response", _TOOL_ERROR) from e


def extract(url: str) -> str:
    """Return the page's full content as markdown, rendered and extracted by Parallel.

    Handles pages local fetching cannot: JavaScript-rendered apps and sites that block plain
    HTTP clients.
    """
    body = {"urls": [url], "advanced_settings": {"full_content": True}}
    data = _post("extract", body, "fetch", timeout=_EXTRACT_TIMEOUT)
    for error in data.get("errors") or []:
        if not isinstance(error, dict):
            continue
        detail = error.get("content") or error.get("error_type") or "unknown error"
        status = error.get("http_status_code")
        suffix = f" (HTTP {status})" if status else ""
        raise ParallelError(f"fetch failed: {detail}{suffix}", page_missing=status in (404, 410))
    for result in data.get("results") or []:
        text = (result.get("full_content") or "") if isinstance(result, dict) else ""
        if text.strip():
            return text
    raise ParallelError("fetch failed: no content returned")
