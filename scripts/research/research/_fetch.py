"""Direct HTTP fetch with content extraction via trafilatura."""

from __future__ import annotations

import httpx
import trafilatura

_TIMEOUT = 15.0
_USER_AGENT = "research-cli/0.1"

# Content-Type prefixes that indicate a binary/file response, not a web page.
_FILE_CONTENT_TYPES = (
    "application/pdf",
    "application/octet-stream",
    "application/zip",
    "application/gzip",
    "application/x-tar",
    "image/",
    "audio/",
    "video/",
)


class FetchError(Exception):
    """HTTP fetch or content extraction failed."""


def fetch_markdown(url: str) -> str:
    """Fetch a URL directly and extract content as clean markdown.

    Raises FetchError on network errors, non-HTML responses, or when
    trafilatura cannot extract meaningful content.
    """
    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
    except httpx.TimeoutException as e:
        raise FetchError("timeout") from e
    except httpx.HTTPStatusError as e:
        raise FetchError(f"HTTP {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise FetchError(f"URL unreachable: {e}") from e

    content_type = response.headers.get("content-type", "")
    if any(content_type.startswith(t) for t in _FILE_CONTENT_TYPES):
        raise FetchError("URL serves a file, not an HTML page; try `research pdf URL` instead")

    markdown = trafilatura.extract(
        response.text,
        output_format="markdown",
        include_links=True,
        include_tables=True,
    )
    if not markdown:
        raise FetchError("no content extracted (page may require JavaScript)")
    return markdown
