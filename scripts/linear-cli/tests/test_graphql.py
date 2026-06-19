"""Tests for _graphql execute error handling and pagination."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from linear_cli._errors import LinearError
from linear_cli._graphql import execute, paginate


def _mock_response(body: dict, headers: dict | None = None, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body
    resp.headers = headers or {}
    resp.raise_for_status = MagicMock()
    return resp


def test_execute_returns_data():
    response = _mock_response({"data": {"viewer": {"id": "u1"}}})
    with patch("linear_cli._graphql.httpx.post", return_value=response):
        data = execute("query { viewer { id } }")

    assert data == {"viewer": {"id": "u1"}}


def test_execute_raises_on_graphql_errors():
    response = _mock_response({"errors": [{"message": "Unauthorized"}]})
    with patch("linear_cli._graphql.httpx.post", return_value=response):
        with pytest.raises(LinearError, match="Unauthorized"):
            execute("query { viewer { id } }")


def test_execute_warns_on_low_rate_limit(capsys):
    response = _mock_response(
        {"data": {"viewer": {"id": "u1"}}},
        headers={"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": "1234567890"},
    )
    with patch("linear_cli._graphql.httpx.post", return_value=response):
        execute("query { viewer { id } }")

    captured = capsys.readouterr()
    assert "rate limit low" in captured.err


def test_execute_no_warn_on_high_rate_limit(capsys):
    response = _mock_response(
        {"data": {"viewer": {"id": "u1"}}},
        headers={"X-RateLimit-Remaining": "500"},
    )
    with patch("linear_cli._graphql.httpx.post", return_value=response):
        execute("query { viewer { id } }")

    captured = capsys.readouterr()
    assert "rate limit" not in captured.err


def test_paginate_follows_cursor():
    """paginate accumulates nodes across two pages."""
    page1 = {
        "issues": {
            "nodes": [{"id": "i1"}, {"id": "i2"}],
            "pageInfo": {"hasNextPage": True, "endCursor": "cursor-abc"},
        }
    }
    page2 = {
        "issues": {
            "nodes": [{"id": "i3"}],
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        }
    }

    call_count = 0

    def fake_execute(query, variables=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            assert variables.get("after") is None
            return page1
        return page2

    with patch("linear_cli._graphql.execute", side_effect=fake_execute):
        nodes = paginate(
            "query { issues { pageInfo { hasNextPage endCursor } nodes { id } } }", {}, ["issues"]
        )

    assert len(nodes) == 3
    assert nodes[0]["id"] == "i1"
    assert nodes[2]["id"] == "i3"
    assert call_count == 2


def test_paginate_single_page():
    page = {
        "issues": {
            "nodes": [{"id": "i1"}],
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        }
    }
    with patch("linear_cli._graphql.execute", return_value=page):
        nodes = paginate("query", {}, ["issues"])

    assert nodes == [{"id": "i1"}]
