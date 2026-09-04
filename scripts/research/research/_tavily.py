"""Tavily client, credentials, search, and remote fetch fallback."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from tavily import TavilyClient

RBW_ITEM = "tavily-api-key"
_DISCOVERY_NOTICE = "[discovery only; fetch a URL before citing it]"

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
    """Return the Tavily API key from env or rbw."""
    import os

    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key
    try:
        result = subprocess.run(
            ["rbw", "get", RBW_ITEM],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise TavilyError("TAVILY_API_KEY not set and `rbw` binary not found") from None
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or f"rbw exited {e.returncode}"
        raise TavilyError(f"failed to read Tavily API key from rbw ({RBW_ITEM}): {msg}") from e
    key = result.stdout.strip()
    if not key:
        raise TavilyError(f"rbw returned empty value for {RBW_ITEM}")
    return key


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


def search(query: str, max_results: int = 5, sourced_answer: bool = True) -> dict:
    """Execute a Tavily search with optional answer generation."""
    try:
        return get_client().search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer="basic" if sourced_answer else False,
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


def format_search_results(results: list[dict], *, include_notice: bool = True) -> str:
    """Format search results as markdown prose."""
    lines: list[str] = []
    for i, r in enumerate(_unique_results(results), 1):
        title = r.get("title") or "Untitled"
        content = r.get("content") or ""
        snippet = content.strip().replace("\n", " ")
        if len(snippet) > 750:
            snippet = snippet[:750] + "..."
        lines.append(f"{i}. {title}\n   URL: {r['url']}\n   {snippet}")
    output = "\n\n".join(lines) if lines else "[no results]"
    return f"{_DISCOVERY_NOTICE}\n\n{output}" if include_notice else output


def format_sourced_answer(response: dict, max_results: int) -> str:
    """Format Tavily's answer and result sources."""
    answer = response.get("answer") or "[no answer]"
    sources = response.get("results", [])
    if not sources:
        return f"{_DISCOVERY_NOTICE}\n\n{answer}"
    formatted = format_search_results(list(sources)[:max_results], include_notice=False)
    return f"{_DISCOVERY_NOTICE}\n\n{answer}\n\n## Sources\n\n{formatted}"
