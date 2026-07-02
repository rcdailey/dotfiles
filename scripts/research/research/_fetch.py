"""Direct HTTP fetch with content extraction via trafilatura."""

from __future__ import annotations

import time
from urllib.parse import urlparse, urlunparse

import click
import trafilatura
from curl_cffi.requests import get as _http_get
from curl_cffi.requests.exceptions import (
    ConnectionError as _CurlConnError,
    RequestException,
    Timeout,
)
from lxml import html as lxml_html

from research._browser import fetch_with_browser

_TIMEOUT = 15.0
_RETRY_DELAY = 1.5  # seconds before retry attempt

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

# Text markers that indicate a bot-challenge page.
_CHALLENGE_MARKERS = (
    "security verification",
    "checking your browser",
    "just a moment",
    "cf-challenge",
    "cf_chl_",
    "challenge-platform",
    "captcha",
    "ddos-guard",
)


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


def _is_challenge_page(text: str) -> bool:
    """Return True if the response body looks like a bot-challenge page."""
    lower = text.lower()
    return any(marker in lower for marker in _CHALLENGE_MARKERS)


def _extract_reddit(html_text: str) -> str:
    """Extract post and comments from old.reddit.com HTML as markdown."""
    try:
        tree = lxml_html.fromstring(html_text)
    except Exception:
        return ""
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


def _fetch_response(url: str) -> object:
    """Fetch URL and return response; raises FetchError on failure.

    Retries once after a short delay on timeout or HTTP 5xx. Non-retryable
    errors (4xx, connection refused) fail immediately.
    """
    for attempt in range(2):
        try:
            response = _http_get(
                url,
                impersonate="safari",
                allow_redirects=True,
                timeout=_TIMEOUT,
            )
            if response.status_code >= 400:
                if response.status_code >= 500 and attempt == 0:
                    time.sleep(_RETRY_DELAY)
                    continue
                raise FetchError(f"HTTP {response.status_code}")
            return response
        except Timeout as e:
            if attempt == 0:
                time.sleep(_RETRY_DELAY)
                continue
            raise FetchError("timeout") from e
        except _CurlConnError as e:
            raise FetchError(f"URL unreachable: {e}") from e
        except RequestException as e:
            raise FetchError(f"URL unreachable: {e}") from e
    raise FetchError("timeout")  # unreachable; satisfies type checker


def fetch_markdown(url: str) -> str:
    """Fetch a URL directly and extract content as clean markdown.

    Raises FetchError on network errors, non-HTML responses, or when
    content extraction fails. Automatically retries with a headless browser
    when the initial response looks like a bot-challenge page.
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
        if not markdown:
            raise FetchError("no content extracted")
        return markdown

    if _is_challenge_page(response.text):
        click.echo("[browser fallback: challenge page detected]", err=True)
        try:
            html = fetch_with_browser(url)
        except Exception as e:
            raise FetchError(f"browser fallback failed: {e}") from e
        markdown = trafilatura.extract(
            html,
            output_format="markdown",
            include_links=True,
            include_tables=True,
        )
        if not markdown:
            raise FetchError("browser fallback failed: no content extracted")
        return markdown

    markdown = trafilatura.extract(
        response.text,
        output_format="markdown",
        include_links=True,
        include_tables=True,
    )

    if not markdown:
        raise FetchError("no content extracted")
    return markdown
