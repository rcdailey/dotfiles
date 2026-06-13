"""Tests for _fetch.py retry logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from research._fetch import FetchError, _fetch_response


def _mock_response(status_code: int = 200, text: str = "ok") -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.headers = {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


def test_fetch_success_first_attempt() -> None:
    resp = _mock_response(200)
    with (
        patch("research._fetch.httpx.get", return_value=resp) as mock_get,
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
            "research._fetch.httpx.get",
            side_effect=[httpx.TimeoutException("timeout"), resp],
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
            "research._fetch.httpx.get",
            side_effect=httpx.TimeoutException("timeout"),
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
            "research._fetch.httpx.get",
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
        patch("research._fetch.httpx.get", return_value=resp_500),
        patch("research._fetch.time.sleep"),
    ):
        with pytest.raises(FetchError, match="HTTP 500"):
            _fetch_response("https://example.com")


def test_no_retry_on_4xx() -> None:
    resp_404 = _mock_response(404)
    with (
        patch("research._fetch.httpx.get", return_value=resp_404) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        with pytest.raises(FetchError, match="HTTP 404"):
            _fetch_response("https://example.com")
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()


def test_no_retry_on_connection_error() -> None:
    with (
        patch(
            "research._fetch.httpx.get",
            side_effect=httpx.ConnectError("connection refused"),
        ) as mock_get,
        patch("research._fetch.time.sleep") as mock_sleep,
    ):
        with pytest.raises(FetchError, match="URL unreachable"):
            _fetch_response("https://example.com")
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()
