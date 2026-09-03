"""Tavily client, credentials, search, and remote fetch fallback."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tavily import TavilyClient

RBW_ITEM = "tavily-api-key"

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


def format_search_results(results: list[dict]) -> str:
    """Format search results as markdown prose."""
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "Untitled"
        content = r.get("content") or ""
        snippet = content.strip().replace("\n", " ")
        if len(snippet) > 750:
            snippet = snippet[:750] + "..."
        lines.append(f"{i}. {title}\n   URL: {r['url']}\n   {snippet}")
    return "\n\n".join(lines) if lines else "[no results]"


def format_sourced_answer(response: dict, max_results: int) -> str:
    """Format Tavily's answer and result sources."""
    answer = response.get("answer") or "[no answer]"
    sources = response.get("results", [])
    if not sources:
        return answer
    return f"{answer}\n\n## Sources\n\n{format_search_results(list(sources)[:max_results])}"
