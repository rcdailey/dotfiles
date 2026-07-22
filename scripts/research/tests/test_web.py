"""Tests for web.py fetch_cmd routing and cache behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from research.cli import cli
from research._cache import _InMemoryCache


def _make_cache(store: dict | None = None) -> MagicMock:
    store = store if store is not None else {}
    cache = MagicMock()
    cache.get.side_effect = lambda k, d=None: store.get(k, d)
    cache.set.side_effect = lambda k, v: store.update({k: v})
    cache.transact.return_value.__enter__ = MagicMock(return_value=None)
    cache.transact.return_value.__exit__ = MagicMock(return_value=False)
    return cache


ENV = {"RESEARCH_SESSION_ID": "test-session"}


def test_fetch_cmd_github_url_reroutes(capsys) -> None:
    """GitHub repo URLs are rerouted to scout orient without fetching."""
    runner = CliRunner()
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research.scout.explore._render_orient") as mock_orient,
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo"],
            env=ENV,
        )
    mock_orient.assert_called_once_with("owner", "repo", ref=None, brief=False)
    assert result.exit_code == 0


def test_fetch_cmd_pdf_url_reroutes() -> None:
    """PDF URLs are rerouted to pdf command without fetching."""
    runner = CliRunner()
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research.pdf._do_pdf") as mock_pdf,
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://example.com/doc.pdf"],
            env=ENV,
        )
    mock_pdf.assert_called_once()
    assert result.exit_code == 0


def test_fetch_cmd_cache_hit_skips_network() -> None:
    """Cached content is returned without any HTTP request."""
    store = {"content:https://example.com": "# Cached Content"}
    runner = CliRunner()
    with (
        patch("research._cache.get_cache", return_value=_make_cache(store)),
        patch("research._fetch._http_get") as mock_http,
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://example.com"],
            env=ENV,
        )
    mock_http.assert_not_called()
    assert "Cached Content" in result.output
    assert result.exit_code == 0


def test_fetch_cmd_github_url_calls_budget_reserve() -> None:
    """GitHub repo reroute charges budget before delegating to scout orient."""
    runner = CliRunner()
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research.web.budget_reserve") as mock_reserve,
        patch("research.scout.explore._render_orient"),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo"],
            env=ENV,
        )
    mock_reserve.assert_called_once_with(
        mock_reserve.call_args[0][0], "https://github.com/owner/repo"
    )
    assert result.exit_code == 0


def test_fetch_cmd_github_discussion_url_calls_budget_reserve() -> None:
    """GitHub discussion reroute charges budget before delegating to scout discussion."""
    runner = CliRunner()
    discussion_data = {
        "number": 1,
        "title": "Test Discussion",
        "body": "body",
        "createdAt": "2024-01-01T00:00:00Z",
        "category": {"name": "General"},
        "comments": [],
    }
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research.web.budget_reserve") as mock_reserve,
        patch("research._ghapi.view_discussion", return_value=discussion_data),
        patch("research.scout.issues._render_comments"),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo/discussions/1"],
            env=ENV,
        )
    mock_reserve.assert_called_once_with(
        mock_reserve.call_args[0][0],
        "https://github.com/owner/repo/discussions/1",
    )
    assert result.exit_code == 0


def test_fetch_cmd_github_issue_url_reroutes() -> None:
    """GitHub issue URLs are rerouted to view_issue."""
    runner = CliRunner()
    issue_data = {
        "number": 42,
        "title": "Bug report",
        "state": "open",
        "createdAt": "2024-01-01T00:00:00Z",
        "body": "body text",
        "comments": [],
    }
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research._ghapi.view_issue", return_value=issue_data),
        patch("research.scout.issues._render_comments"),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo/issues/42"],
            env=ENV,
        )
    assert result.exit_code == 0
    assert "Bug report" in result.output


def test_fetch_cmd_github_pr_url_reroutes() -> None:
    """GitHub PR URLs are rerouted to view_pr."""
    runner = CliRunner()
    pr_data = {
        "number": 7,
        "title": "Fix everything",
        "state": "merged",
        "createdAt": "2024-01-01T00:00:00Z",
        "mergedAt": "2024-01-02T00:00:00Z",
        "body": "pr body",
        "comments": [],
    }
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research._ghapi.view_pr", return_value=pr_data),
        patch("research.scout.issues._render_comments"),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo/pull/7"],
            env=ENV,
        )
    assert result.exit_code == 0
    assert "Fix everything" in result.output


def test_fetch_cmd_github_commit_url_reroutes() -> None:
    """GitHub commit URLs are rerouted to view_commit."""
    runner = CliRunner()
    commit_data = {
        "commit": {
            "message": "fix: resolve the issue",
            "author": {"name": "Alice", "date": "2024-01-01T00:00:00Z"},
            "committer": {"name": "Alice", "date": "2024-01-01T00:00:00Z"},
        },
        "stats": {"additions": 5, "deletions": 2},
        "files": [],
    }
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research._ghapi.view_commit", return_value=commit_data),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo/commit/abc1234"],
            env=ENV,
        )
    assert result.exit_code == 0
    assert "fix: resolve the issue" in result.output


def test_fetch_cmd_github_blob_url_reroutes() -> None:
    """GitHub blob URLs are rerouted to clone-based cat."""
    runner = CliRunner()
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "file content here\n"
    with (
        patch("research._cache.get_cache", return_value=_make_cache()),
        patch("research.scout._clone.ensure_repo", return_value=MagicMock()),
        patch("research.scout._clone.ensure_ref", return_value="deadbeef"),
        patch("subprocess.run", return_value=mock_proc),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://github.com/owner/repo/blob/main/src/foo.py"],
            env=ENV,
        )
    assert result.exit_code == 0
    assert "file content here" in result.output


# --- _InMemoryCache tests ---


def test_in_memory_cache_get_set() -> None:
    cache = _InMemoryCache()
    assert cache.get("key") is None
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_in_memory_cache_delete() -> None:
    cache = _InMemoryCache()
    cache.set("key", "value")
    cache.delete("key")
    assert cache.get("key") is None


def test_in_memory_cache_contains() -> None:
    cache = _InMemoryCache()
    cache.set("key", "value")
    assert "key" in cache
    assert "other" not in cache


def test_in_memory_cache_iter() -> None:
    cache = _InMemoryCache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert set(cache) == {"a", "b"}


def test_in_memory_cache_transact() -> None:
    cache = _InMemoryCache()
    with cache.transact():
        cache.set("key", "val")
    assert cache.get("key") == "val"


def test_fetch_cmd_fetches_and_caches() -> None:
    """Uncached URL fetches content and stores it."""
    store: dict = {}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    runner = CliRunner()
    with (
        patch("research._cache.get_cache", return_value=_make_cache(store)),
        patch("research._budget.budget_reserve"),
        patch("research._fetch._http_get", return_value=mock_response),
        patch("trafilatura.extract", return_value="Hello world"),
    ):
        result = runner.invoke(
            cli,
            ["web", "fetch", "https://example.com"],
            env=ENV,
        )
    assert "content:https://example.com" in store
    assert result.exit_code == 0
