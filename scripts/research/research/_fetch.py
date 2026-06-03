"""Direct HTTP fetch with content extraction via trafilatura."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

import httpx
import trafilatura
from lxml import html as lxml_html

_TIMEOUT = 15.0
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

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

_REDDIT_HOSTS = ("www.reddit.com", "reddit.com", "old.reddit.com")


class FetchError(Exception):
    """HTTP fetch or content extraction failed."""


def _is_reddit(url: str) -> bool:
    return urlparse(url).hostname in _REDDIT_HOSTS


def _to_old_reddit(url: str) -> str:
    """Rewrite reddit.com URLs to old.reddit.com for server-rendered HTML."""
    parsed = urlparse(url)
    if parsed.hostname in ("www.reddit.com", "reddit.com"):
        return urlunparse(parsed._replace(netloc="old.reddit.com"))
    return url


def _extract_reddit(html_text: str) -> str:
    """Extract post and comments from old.reddit.com HTML as markdown."""
    tree = lxml_html.fromstring(html_text)
    parts: list[str] = []

    # Post title
    titles = tree.xpath('//a[contains(@class, "title")]/text()')
    if titles:
        parts.append(f"# {titles[0].strip()}")

    # Post body (selftext)
    bodies = tree.xpath('//div[contains(@class, "expando")]//div[contains(@class, "md")]')
    if bodies:
        text = bodies[0].text_content().strip()
        if text:
            parts.append(text)

    # Comments
    entries = tree.xpath('//div[contains(@class, "comment")]//div[contains(@class, "entry")]')
    if entries:
        parts.append("---\n\n## Comments")
        for entry in entries:
            authors = entry.xpath('.//a[contains(@class, "author")]/text()')
            comment_bodies = entry.xpath(
                './/div[contains(@class, "usertext-body")]//div[contains(@class, "md")]'
            )
            if authors and comment_bodies:
                author = authors[0].strip()
                body = comment_bodies[0].text_content().strip()
                parts.append(f"**{author}:**\n\n{body}")

    return "\n\n".join(parts)


def _fetch_response(url: str) -> httpx.Response:
    """Fetch URL and return response; raises FetchError on failure."""
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
    return response


def fetch_markdown(url: str) -> str:
    """Fetch a URL directly and extract content as clean markdown.

    Raises FetchError on network errors, non-HTML responses, or when
    content extraction fails.
    """
    is_reddit = _is_reddit(url)
    if is_reddit:
        url = _to_old_reddit(url)

    response = _fetch_response(url)

    content_type = response.headers.get("content-type", "")
    if any(content_type.startswith(t) for t in _FILE_CONTENT_TYPES):
        raise FetchError("URL serves a file, not an HTML page; try `research pdf URL` instead")

    if is_reddit:
        markdown = _extract_reddit(response.text)
    else:
        markdown = trafilatura.extract(
            response.text,
            output_format="markdown",
            include_links=True,
            include_tables=True,
        )

    if not markdown:
        raise FetchError("no content extracted (page may require JavaScript)")
    return markdown
