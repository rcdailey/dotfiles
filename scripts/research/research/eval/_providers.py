"""Web search provider adapters with one request shape and one result shape.

Every adapter receives the same replayed query and filters and returns ranked results as
`{"url", "title", "snippet"}`. Settings follow each provider's documented default or
recommendation for agent search; the per-adapter notes name every deviation. Parallel runs
through the researcher's production adapter, so its rows measure the shipped configuration.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from curl_cffi import requests

from research import _parallel as parallel
from research._secrets import read_secret

MAX_RESULTS = 10
_TIMEOUT = 60
_DAYS = {"day": 1, "week": 7, "month": 31, "year": 365}


class ProviderError(Exception):
    """A provider request failed."""


@dataclass(frozen=True)
class Query:
    """One replayed researcher search: its text and the filters it was sent with."""

    query: str
    domains: list[str]
    exclude_domains: list[str]
    time_range: str | None

    @property
    def since(self) -> str | None:
        if not self.time_range:
            return None
        today = datetime.now(UTC).date()
        return (today - timedelta(days=_DAYS[self.time_range])).isoformat()


def _key(name: str) -> str:
    return read_secret(f"{name.upper()}_API_KEY", f"{name}-api-key")


def post_json(url: str, body: dict, headers: dict) -> dict:
    return _request("POST", url, headers=headers, json=body)


def _request(method: str, url: str, **kwargs: object) -> dict:
    """Send one request, retrying once after a rate limit or server error."""
    for attempt in range(2):
        try:
            response = requests.request(method, url, timeout=_TIMEOUT, **kwargs)
        except requests.RequestsError as e:
            if attempt == 0:
                time.sleep(3)
                continue
            raise ProviderError(f"request failed: {e}") from e
        retryable = response.status_code == 429 or response.status_code >= 500
        if retryable and attempt == 0:
            time.sleep(float(response.headers.get("retry-after") or 5))
            continue
        if response.status_code >= 400:
            raise ProviderError(f"HTTP {response.status_code}: {response.text[:300]}")
        return response.json()
    raise ProviderError("retry exhausted")


def _sites(q: Query) -> str:
    """Express domain filters as query operators for providers without filter fields."""
    include = " OR ".join(f"site:{d}" for d in q.domains)
    exclude = " ".join(f"-site:{d}" for d in q.exclude_domains)
    return " ".join(part for part in (include, q.query, exclude) if part)


def tavily(q: Query) -> list[dict]:
    """Production settings: advanced depth, two chunks per source."""
    body = {
        "query": q.query,
        "search_depth": "advanced",
        "chunks_per_source": 2,
        "max_results": MAX_RESULTS,
        "include_domains": q.domains or None,
        "exclude_domains": q.exclude_domains or None,
        "time_range": q.time_range,
    }
    data = post_json(
        "https://api.tavily.com/search",
        {k: v for k, v in body.items() if v is not None},
        {"Authorization": f"Bearer {_key('tavily')}"},
    )
    return [
        {"url": r["url"], "title": r.get("title", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])
    ]


def exa(q: Query) -> list[dict]:
    """Auto search type with highlights, Exa's documented default for agents."""
    body: dict = {
        "query": q.query,
        "type": "auto",
        "numResults": MAX_RESULTS,
        "contents": {"highlights": True},
    }
    if q.domains:
        body["includeDomains"] = q.domains
    if q.exclude_domains:
        body["excludeDomains"] = q.exclude_domains
    if q.since:
        body["startPublishedDate"] = f"{q.since}T00:00:00.000Z"
    data = post_json("https://api.exa.ai/search", body, {"x-api-key": _key("exa")})
    return [
        {
            "url": r["url"],
            "title": r.get("title") or "",
            "snippet": " ".join(r.get("highlights") or []) or r.get("text", ""),
        }
        for r in data.get("results", [])
    ]


def brave(q: Query) -> list[dict]:
    """Web search; domain filters become site: operators because the API has no filter field."""
    params = {"q": _sites(q), "count": MAX_RESULTS, "extra_snippets": "true"}
    if q.time_range:
        params["freshness"] = {"day": "pd", "week": "pw", "month": "pm", "year": "py"}[q.time_range]
    data = _request(
        "GET",
        "https://api.search.brave.com/res/v1/web/search",
        params=params,
        headers={"X-Subscription-Token": _key("brave"), "Accept": "application/json"},
    )
    return [
        {
            "url": r["url"],
            "title": r.get("title", ""),
            "snippet": " ".join([r.get("description", ""), *(r.get("extra_snippets") or [])]),
        }
        for r in (data.get("web") or {}).get("results", [])
    ]


def firecrawl(q: Query) -> list[dict]:
    """Search without scraping, so results carry only Firecrawl's descriptions."""
    source: dict = {"type": "web"}
    if q.time_range:
        source["tbs"] = f"qdr:{q.time_range[0]}"
    body: dict = {"query": q.query, "limit": MAX_RESULTS, "sources": [source]}
    # The API rejects include and exclude filters together; inclusion is the stronger intent.
    if q.domains:
        body["includeDomains"] = q.domains
    elif q.exclude_domains:
        body["excludeDomains"] = q.exclude_domains
    data = post_json(
        "https://api.firecrawl.dev/v2/search",
        body,
        {"Authorization": f"Bearer {_key('firecrawl')}"},
    )
    return [
        {"url": r["url"], "title": r.get("title", ""), "snippet": r.get("description", "")}
        for r in (data.get("data") or {}).get("web", [])
    ]


def linkup(q: Query) -> list[dict]:
    """Standard depth, raw search results (the setting the researcher used before Tavily)."""
    body: dict = {
        "q": q.query,
        "depth": "standard",
        "outputType": "searchResults",
        "maxResults": MAX_RESULTS,
    }
    if q.domains:
        body["includeDomains"] = q.domains
    if q.exclude_domains:
        body["excludeDomains"] = q.exclude_domains
    if q.since:
        body["fromDate"] = q.since
    data = post_json(
        "https://api.linkup.so/v1/search", body, {"Authorization": f"Bearer {_key('linkup')}"}
    )
    return [
        {"url": r["url"], "title": r.get("name", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])
    ]


def _parallel(mode: str) -> Callable[[Query], list[dict]]:
    def search(q: Query) -> list[dict]:
        # The production adapter, so the harness measures exactly what the researcher ships.
        try:
            results = parallel.search(
                q.query,
                MAX_RESULTS,
                tuple(q.domains),
                tuple(q.exclude_domains),
                q.time_range,
                mode=mode,
            )
        except parallel.ParallelError as e:
            raise ProviderError(str(e)) from e
        return [{"url": r["url"], "title": r["title"], "snippet": r["content"]} for r in results]

    search.__doc__ = f"Production adapter in {mode} mode."
    return search


def perplexity(q: Query) -> list[dict]:
    """Search API with domain and recency filters."""
    body: dict = {"query": q.query, "max_results": MAX_RESULTS}
    domain_filter = [*q.domains, *(f"-{d}" for d in q.exclude_domains)]
    if domain_filter:
        body["search_domain_filter"] = domain_filter
    if q.time_range:
        body["search_recency_filter"] = q.time_range
    data = post_json(
        "https://api.perplexity.ai/search",
        body,
        {"Authorization": f"Bearer {_key('perplexity')}"},
    )
    return [
        {"url": r["url"], "title": r.get("title", ""), "snippet": r.get("snippet", "")}
        for r in data.get("results", [])
    ]


def keenable(q: Query) -> list[dict]:
    """Default pro mode; several domains become site: operators, as Keenable documents."""
    body: dict = {"query": q.query, "max_results": MAX_RESULTS}
    if len(q.domains) == 1:
        body["site"] = q.domains[0]
    elif q.domains:
        body["query"] = " ".join([*(f"site:{d}" for d in q.domains), q.query])
    if q.exclude_domains:
        body["exclude_domains"] = q.exclude_domains
    if q.time_range:
        body["published_after"] = f"{_DAYS[q.time_range]}d"
    data = post_json("https://api.keenable.ai/v1/search", body, {"X-API-Key": _key("keenable")})
    return [
        {"url": r["url"], "title": r.get("title", ""), "snippet": r.get("snippet", "")}
        for r in data.get("results", [])
    ]


PROVIDERS: dict[str, Callable[[Query], list[dict]]] = {
    "tavily": tavily,
    "exa": exa,
    "brave": brave,
    "firecrawl": firecrawl,
    "linkup": linkup,
    "parallel-turbo": _parallel("turbo"),
    "parallel-fast": _parallel("fast"),
    "parallel-basic": _parallel("basic"),
    "parallel-advanced": _parallel("advanced"),
    "perplexity": perplexity,
    "keenable": keenable,
}
