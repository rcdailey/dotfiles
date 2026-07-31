"""Headless browser fetch via Playwright for JS-gated pages.

All playwright imports are lazy. If the Python packages are missing, they are
auto-installed via uv on first use. If the Chromium browser binary is missing,
``playwright install chromium`` runs automatically.
"""

from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import click

_BROWSER_TIMEOUT = 30_000  # milliseconds
_CHALLENGE_SETTLE = 3_000  # milliseconds; wait for challenge redirect

_PACKAGES = ["playwright>=1.50", "playwright-stealth>=2.0"]

_pw: Any = None
_browser: Any = None
_stealth: Any = None


def _ensure_packages() -> None:
    """Install playwright packages via uv if not importable."""
    try:
        import playwright
        import playwright_stealth
    except ImportError:
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError(
                "playwright is not installed and uv is not available to auto-install it"
            )
        click.echo("[installing playwright packages]", err=True)
        result = subprocess.run(
            [uv, "pip", "install", "--python", sys.executable, *_PACKAGES],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"failed to install playwright packages: {result.stderr.strip()}")
        # Verify the install worked
        try:
            import playwright  # noqa: F401
            import playwright_stealth  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                f"playwright packages installed but still not importable: {e}"
            ) from e


def _ensure_browser(pw: Any) -> None:
    """Install Chromium browser binary if missing."""
    if Path(pw.chromium.executable_path).exists():
        return
    click.echo("[installing chromium browser]", err=True)
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to install chromium: {result.stderr.strip()}")
    if not Path(pw.chromium.executable_path).exists():
        raise RuntimeError(
            "playwright install chromium succeeded but binary not found at "
            f"{pw.chromium.executable_path}"
        )


def _get_browser() -> Any:
    """Return a singleton browser instance, launching on first call.

    Auto-installs Python packages and Chromium binary as needed.
    """
    global _pw, _browser

    if _browser is not None and _browser.is_connected():
        return _browser

    _ensure_packages()
    from playwright.sync_api import sync_playwright

    _pw = sync_playwright().start()
    _ensure_browser(_pw)
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
    Auto-installs Python packages and Chromium binary on first use if missing.
    """
    global _stealth

    browser = _get_browser()
    if _stealth is None:
        from playwright_stealth import Stealth

        _stealth = Stealth()
    context = browser.new_context()
    _stealth.apply_stealth_sync(context)
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=_BROWSER_TIMEOUT)
        page.wait_for_timeout(_CHALLENGE_SETTLE)
        return page.content()
    finally:
        context.close()
