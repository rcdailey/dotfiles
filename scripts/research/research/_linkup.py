"""Linkup client and API key resolution."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from research._errors import die

if TYPE_CHECKING:
    from linkup import LinkupClient

RBW_ITEM = "linkup-api-key"

_ERROR_MESSAGES = {
    "LinkupAuthenticationError": "authentication failed",
    "LinkupInsufficientCreditError": "out of credit (billing issue)",
    "LinkupInvalidRequestError": "invalid request",
    "LinkupNoResultError": "no results",
    "LinkupPaymentRequiredError": "payment required",
    "LinkupTimeoutError": "timeout",
    "LinkupTooManyRequestsError": "rate limited, try again later",
}


def get_linkup_api_key() -> str:
    """Return the Linkup API key from env or rbw."""
    import os

    key = os.environ.get("LINKUP_API_KEY")
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
        die("LINKUP_API_KEY not set and `rbw` binary not found")
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or f"rbw exited {e.returncode}"
        die(f"failed to read Linkup API key from rbw ({RBW_ITEM}): {msg}")
    key = result.stdout.strip()
    if not key:
        die(f"rbw returned empty value for {RBW_ITEM}")
    return key


def get_client() -> LinkupClient:
    """Return a configured LinkupClient."""
    from linkup import LinkupClient

    return LinkupClient(api_key=get_linkup_api_key())


def translate_error(action: str, e: Exception) -> str:
    """Translate backend-specific exceptions into agent-facing messages."""
    from research._render import format_error

    name = type(e).__name__
    reason = _ERROR_MESSAGES.get(name)
    if reason is None:
        clean = name[6:] if name.startswith("Linkup") else name
        reason = f"{clean}: {e}"
    return format_error(action, reason)


def search(query: str, max_results: int = 5) -> list:
    """Execute a Linkup search and return results."""
    client = get_client()
    try:
        response = client.search(
            query=query,
            depth="standard",
            output_type="searchResults",
            max_results=max_results,
        )
        return response.results
    except Exception as e:
        raise SearchError(translate_error("search", e)) from e


class SearchError(Exception):
    """Search operation failed."""

    pass


def format_search_results(results: list) -> str:
    """Format search results as markdown prose."""
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        if getattr(r, "type", None) == "image":
            lines.append(f"{i}. [image] {r.name}\n   URL: {r.url}")
            continue
        content = getattr(r, "content", "") or ""
        snippet = content.strip().replace("\n", " ")
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        lines.append(f"{i}. {r.name}\n   URL: {r.url}\n   {snippet}")
    return "\n\n".join(lines) if lines else "[no results]"
