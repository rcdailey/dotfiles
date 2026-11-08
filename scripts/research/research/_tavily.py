"""Tavily client, credentials, search, and remote fetch fallback."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from tavily import TavilyClient

RBW_ITEM = "tavily-api-key"
_DISCOVERY_NOTICE = "[discovery only; fetch a URL before citing it]"
# Tavily's own knowledge pages match many queries without answering any of them.
_ALWAYS_EXCLUDED = ("tavily.com",)
# Measured on replayed researcher queries: keeps ~90% of on-topic results, drops ~75% of noise.
MIN_SCORE = 0.3

_ERROR_MESSAGES = {
    "InvalidAPIKeyError": "authentication failed",
    "UsageLimitExceededError": "rate limited or out of credit",
    "TavilyKeylessLimitError": "rate limited",
    "BadRequestError": "invalid request",
    "ForbiddenError": "request forbidden",
    "TimeoutError": "timeout",
}


class TavilyError(Exception):
    """Tavily operation failed."""


def get_tavily_api_key() -> str:
    """Return the Tavily API key from env or rbw.

    Concurrent invocations share one unlock prompt: the serializing pinentry
    wrapper cancels the queued prompts once the vault is open, so a cancelled
    first attempt is retried once against the now-unlocked agent.
    """
    import os

    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key
    try:
        result = _rbw_get()
    except FileNotFoundError:
        raise TavilyError("TAVILY_API_KEY not set and `rbw` binary not found") from None
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or f"rbw exited {e.returncode}"
        raise TavilyError(f"failed to read Tavily API key from rbw ({RBW_ITEM}): {msg}") from e
    key = result.stdout.strip()
    if not key:
        raise TavilyError(f"rbw returned empty value for {RBW_ITEM}")
    return key


def _rbw_get() -> subprocess.CompletedProcess[str]:
    cmd = ["rbw", "get", RBW_ITEM]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        if "pinentry cancelled" not in e.stderr:
            raise
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def get_client() -> TavilyClient:
    """Return a configured Tavily client."""
    from tavily import TavilyClient

    return TavilyClient(api_key=get_tavily_api_key())


def translate_error(action: str, e: Exception) -> str:
    """Translate backend-specific exceptions into agent-facing messages."""
    name = type(e).__name__
    reason = _ERROR_MESSAGES.get(name)
    if reason is None:
        clean = name.removeprefix("Tavily")
        reason = clean or "request failed"
    return f"{action} failed: {reason}"


def search(
    query: str,
    max_results: int,
    domains: tuple[str, ...] = (),
    exclude_domains: tuple[str, ...] = (),
    time_range: str | None = None,
    exact_match: bool = False,
) -> dict:
    """Execute a Tavily search and return its ranked results.

    `domains` restricts results to those sites; `exact_match` requires quoted phrases in the query
    to appear verbatim in each result. Searches always use advanced depth (2 credits): replayed
    researcher queries found about 70% more relevant pages than basic depth.
    """
    try:
        return get_client().search(
            query=query,
            search_depth="advanced",
            chunks_per_source=2,
            max_results=max_results,
            include_domains=list(domains) or None,
            exclude_domains=[*exclude_domains, *_ALWAYS_EXCLUDED],
            time_range=time_range,
            exact_match=exact_match or None,
        )
    except TavilyError:
        raise
    except Exception as e:
        raise TavilyError(translate_error("search", e)) from e


def fetch_markdown(url: str) -> str:
    """Fetch page markdown through Tavily Extract."""
    try:
        response = get_client().extract(
            urls=[url],
            extract_depth="advanced",
            format="markdown",
        )
    except TavilyError:
        raise
    except Exception as e:
        raise TavilyError(translate_error("fetch", e)) from e

    results = response.get("results", [])
    if not results:
        raise TavilyError("fetch failed: no content returned")
    text = results[0].get("raw_content", "") or ""
    if not text.strip():
        raise TavilyError("fetch failed: no content returned")
    return text


def _result_identity(url: str) -> tuple[str, str, str, str]:
    """Return a stable identity for common equivalent result URLs."""
    parsed = urlsplit(url)
    scheme = "" if parsed.scheme.lower() in ("http", "https") else parsed.scheme.lower()
    host = (parsed.hostname or parsed.netloc).lower().removeprefix("www.")
    if parsed.port and (parsed.scheme.lower(), parsed.port) not in (("http", 80), ("https", 443)):
        host = f"{host}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/"
    return scheme, host, path, parsed.query


def _unique_results(results: list[dict]) -> list[dict]:
    """Keep the first search result for each canonical URL."""
    unique = []
    seen = set()
    for result in results:
        identity = _result_identity(result["url"])
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(result)
    return unique


def format_search_results(results: list[dict]) -> str:
    """Format relevant search results as markdown prose, noting how many were hidden.

    Results without a score (backends that do not rank by relevance) are always shown.
    """
    unique = _unique_results(results)
    relevant = [r for r in unique if r.get("score", MIN_SCORE) >= MIN_SCORE]
    lines: list[str] = []
    for i, r in enumerate(relevant, 1):
        title = r.get("title") or "Untitled"
        snippet = (r.get("content") or "").strip().replace("\n", " ")
        score = f" (score {r['score']:.2f})" if "score" in r else ""
        lines.append(f"{i}. {title}{score}\n   Discovered: {r['url']}\n   {snippet}")
    output = "\n\n".join(lines) if lines else "[no results]"
    hidden = len(unique) - len(relevant)
    if hidden:
        output += f"\n\n[{hidden} results below relevance score {MIN_SCORE} hidden]"
    return f"{_DISCOVERY_NOTICE}\n\n{output}"
