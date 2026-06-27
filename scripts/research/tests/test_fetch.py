"""Tests for _fetch.py retry logic, challenge detection, and browser fallback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from curl_cffi.requests.exceptions import (
    ConnectionError as CurlConnError,
    Timeout,
)

from research._fetch import FetchError, _fetch_response, _is_challenge_page, fetch_markdown


def _mock_response(status_code: int = 200, text: str = "ok") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = {}
    return resp


# ---------------------------------------------------------------------------
# _fetch_response: retry logic
# ---------------------------------------------------------------------------


def test_fetch_success_first_attempt() -> None:
    resp = _mock_response(200)
    with (
        patch("research._fetch._http_get", return_value=resp) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        result = _fetch_response("https://example.com")
    assert result is resp
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()


def test_retry_on_timeout_succeeds_second_attempt() -> None:
    resp = _mock_response(200)
    with (
        patch(
            "research._fetch._http_get",
            side_effect=[Timeout("timeout"), resp],
        ) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        result = _fetch_response("https://example.com")
    assert result is resp
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


def test_retry_on_timeout_fails_both_attempts() -> None:
    with (
        patch(
            "research._fetch._http_get",
            side_effect=Timeout("timeout"),
        ),
        patch("research._fetch.time.sleep"),
    ):
        with pytest.raises(FetchError, match="timeout"):
            _fetch_response("https://example.com")


def test_retry_on_5xx_succeeds_second_attempt() -> None:
    resp_503 = _mock_response(503)
    resp_ok = _mock_response(200)
    with (
        patch(
            "research._fetch._http_get",
            side_effect=[resp_503, resp_ok],
        ) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        result = _fetch_response("https://example.com")
    assert result is resp_ok
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()


def test_retry_on_5xx_fails_both_attempts() -> None:
    resp_500 = _mock_response(500)
    with (
        patch("research._fetch._http_get", return_value=resp_500),
        patch("research._fetch.time.sleep"),
    ):
        with pytest.raises(FetchError, match="HTTP 500"):
            _fetch_response("https://example.com")


def test_no_retry_on_4xx() -> None:
    resp_404 = _mock_response(404)
    with (
        patch("research._fetch._http_get", return_value=resp_404) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        with pytest.raises(FetchError, match="HTTP 404"):
            _fetch_response("https://example.com")
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()


def test_no_retry_on_connection_error() -> None:
    with (
        patch(
            "research._fetch._http_get",
            side_effect=CurlConnError("connection refused"),
        ) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        with pytest.raises(FetchError, match="URL unreachable"):
            _fetch_response("https://example.com")
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# _is_challenge_page: detection heuristic
# ---------------------------------------------------------------------------


def test_challenge_detected_checking_your_browser() -> None:
    assert _is_challenge_page("<html>Checking your browser before accessing...</html>")


def test_challenge_detected_just_a_moment() -> None:
    assert _is_challenge_page("<html><title>Just a moment...</title></html>")


def test_challenge_detected_security_verification() -> None:
    assert _is_challenge_page("Please complete security verification to continue.")


def test_challenge_detected_cf_challenge() -> None:
    assert _is_challenge_page('<div class="cf-challenge-running"></div>')


def test_challenge_not_detected_normal_page() -> None:
    assert not _is_challenge_page("<html><body><p>Hello world</p></body></html>")


def test_challenge_detection_case_insensitive() -> None:
    assert _is_challenge_page("CHECKING YOUR BROWSER")


# ---------------------------------------------------------------------------
# fetch_markdown: browser fallback integration
# ---------------------------------------------------------------------------


def test_browser_fallback_triggered_on_challenge_page() -> None:
    """When curl_cffi returns a challenge page, browser fallback is invoked."""
    challenge_html = "<html><title>Just a moment...</title></html>"
    rendered_html = "<html><body><article>Real content here for extraction.</article></body></html>"

    resp = _mock_response(200, challenge_html)

    with (
        patch("research._fetch._http_get", return_value=resp),
        patch("research._fetch.fetch_with_browser", return_value=rendered_html) as mock_browser,
        patch(
            "research._fetch.trafilatura.extract", return_value="Real content here"
        ) as mock_extract,
        patch("research._fetch.click.echo") as mock_echo,
    ):
        result = fetch_markdown("https://example.com")

    assert result == "Real content here"
    mock_browser.assert_called_once_with("https://example.com")
    mock_echo.assert_called_once_with("[browser fallback: challenge page detected]", err=True)
    mock_extract.assert_called_once_with(
        rendered_html,
        output_format="markdown",
        include_links=True,
        include_tables=True,
    )


def test_browser_fallback_raises_when_browser_fails() -> None:
    """FetchError raised with browser fallback message when browser fails."""
    challenge_html = "<html><title>Just a moment...</title></html>"
    resp = _mock_response(200, challenge_html)

    with (
        patch("research._fetch._http_get", return_value=resp),
        patch("research._fetch.fetch_with_browser", side_effect=RuntimeError("browser crashed")),
        patch("research._fetch.click.echo"),
    ):
        with pytest.raises(FetchError, match="browser fallback failed"):
            fetch_markdown("https://example.com")


def test_browser_fallback_raises_when_no_content_extracted() -> None:
    """FetchError raised when browser renders page but trafilatura finds nothing."""
    challenge_html = "<html><title>Just a moment...</title></html>"
    resp = _mock_response(200, challenge_html)

    with (
        patch("research._fetch._http_get", return_value=resp),
        patch("research._fetch.fetch_with_browser", return_value="<html></html>"),
        patch("research._fetch.trafilatura.extract", return_value=None),
        patch("research._fetch.click.echo"),
    ):
        with pytest.raises(FetchError, match="browser fallback failed: no content extracted"):
            fetch_markdown("https://example.com")


def test_no_browser_fallback_for_normal_page() -> None:
    """Browser is not invoked for pages that pass challenge detection."""
    normal_html = "<html><body><p>Hello world, this is normal content.</p></body></html>"
    resp = _mock_response(200, normal_html)

    with (
        patch("research._fetch._http_get", return_value=resp),
        patch("research._fetch.fetch_with_browser") as mock_browser,
        patch("research._fetch.trafilatura.extract", return_value="Hello world"),
    ):
        result = fetch_markdown("https://example.com")

    assert result == "Hello world"
    mock_browser.assert_not_called()
