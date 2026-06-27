"""Headless browser fetch via Playwright for JS-gated pages."""

from __future__ import annotations

import atexit

from playwright.sync_api import Browser, Playwright, sync_playwright
from playwright_stealth import Stealth

_BROWSER_TIMEOUT = 30_000  # milliseconds
_CHALLENGE_SETTLE = 3_000  # milliseconds; wait for challenge redirect

_pw: Playwright | None = None
_browser: Browser | None = None
_stealth = Stealth()


def _get_browser() -> Browser:
    """Return a singleton browser instance, launching on first call."""
    global _pw, _browser
    if _browser is None or not _browser.is_connected():
        _pw = sync_playwright().start()
        _browser = _pw.chromium.launch(headless=True)
        atexit.register(_shutdown)
    return _browser


def _shutdown() -> None:
    global _pw, _browser
    if _browser:
        _browser.close()
        _browser = None
    if _pw:
        _pw.stop()
        _pw = None


def fetch_with_browser(url: str) -> str:
    """Fetch URL using a headless Chromium browser; returns rendered HTML.

    Uses a singleton browser process (launched once, reused across calls).
    Applies stealth patches to avoid bot detection of headless Chromium.
    Requires Playwright's Chromium (``playwright install chromium``).
    """
    browser = _get_browser()
    context = browser.new_context()
    _stealth.apply_stealth_sync(context)
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=_BROWSER_TIMEOUT)
        page.wait_for_timeout(_CHALLENGE_SETTLE)
        return page.content()
    finally:
        context.close()
