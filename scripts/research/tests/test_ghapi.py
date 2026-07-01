"""Tests for _ghapi.py."""

from __future__ import annotations

from unittest.mock import patch

from research._ghapi import list_discussions


def _make_graphql_response(nodes: list[dict]) -> dict:
    return {"data": {"repository": {"discussions": {"nodes": nodes}}}}


def _make_discussion(title: str, number: int = 1) -> dict:
    return {
        "number": number,
        "title": title,
        "createdAt": "2024-01-01T00:00:00Z",
        "author": {"login": "user"},
        "category": {"name": "General"},
    }


# ---------------------------------------------------------------------------
# list_discussions: search fetch-limit amplification and client-side filtering
# ---------------------------------------------------------------------------


def test_list_discussions_search_fetches_amplified_limit() -> None:
    """With search, graphql is called with min(limit*3, 100) so filtering has headroom."""
    nodes = [_make_discussion("needle post", i) for i in range(20)]
    response = _make_graphql_response(nodes)

    with patch("research._ghapi.graphql", return_value=response) as mock_gql:
        list_discussions("owner", "repo", search="needle", limit=5)

    _, kwargs = mock_gql.call_args
    assert kwargs["limit"] == "15"  # min(5*3, 100)


def test_list_discussions_search_caps_amplified_limit_at_100() -> None:
    """Amplified fetch limit never exceeds 100."""
    response = _make_graphql_response([])

    with patch("research._ghapi.graphql", return_value=response) as mock_gql:
        list_discussions("owner", "repo", search="x", limit=50)

    _, kwargs = mock_gql.call_args
    assert kwargs["limit"] == "100"  # min(50*3=150, 100)


def test_list_discussions_search_filters_and_truncates() -> None:
    """Only title-matching results are returned, capped at limit."""
    nodes = [_make_discussion(f"needle post {i}", i) for i in range(10)] + [
        _make_discussion(f"unrelated post {i}", i + 100) for i in range(10)
    ]
    response = _make_graphql_response(nodes)

    with patch("research._ghapi.graphql", return_value=response):
        results = list_discussions("owner", "repo", search="needle", limit=5)

    assert len(results) == 5
    assert all("needle" in r["title"].lower() for r in results)


def test_list_discussions_no_search_uses_exact_limit() -> None:
    """Without search, graphql receives the exact limit (no amplification)."""
    response = _make_graphql_response([_make_discussion("any post", 1)])

    with patch("research._ghapi.graphql", return_value=response) as mock_gql:
        list_discussions("owner", "repo", limit=10)

    _, kwargs = mock_gql.call_args
    assert kwargs["limit"] == "10"


def test_list_discussions_search_no_matches_returns_empty() -> None:
    """Returns empty list when no titles match the search term."""
    nodes = [_make_discussion("unrelated", i) for i in range(5)]
    response = _make_graphql_response(nodes)

    with patch("research._ghapi.graphql", return_value=response):
        results = list_discussions("owner", "repo", search="needle", limit=5)

    assert results == []
