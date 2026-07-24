"""Tests for scout/search.py."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from research._ghapi import APIError
from research.cli import cli as root_cli


def _gh_result(stdout: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def _repo(
    full_name: str = "twpayne/chezmoi",
    stars: int = 1234,
    forks: int = 56,
    pushed: str = "2024-05-01T00:00:00Z",
    updated: str = "2024-05-02T00:00:00Z",
    language: str = "Go",
    description: str = "dotfiles manager",
    archived: bool = False,
) -> dict:
    return {
        "fullName": full_name,
        "stargazersCount": stars,
        "forksCount": forks,
        "pushedAt": pushed,
        "updatedAt": updated,
        "language": language,
        "description": description,
        "isArchived": archived,
    }


def test_search_shows_stars_pushed_and_forks() -> None:
    runner = CliRunner()
    repos = [_repo()]

    with patch(
        "research.scout.search._run_gh", return_value=_gh_result(json.dumps(repos))
    ) as mock_gh:
        result = runner.invoke(root_cli, ["scout", "search", "chezmoi dotfiles", "--limit", "3"])

    assert result.exit_code == 0
    assert "twpayne/chezmoi" in result.output
    assert "stars: 1234" in result.output
    assert "forks: 56" in result.output
    assert "last push: 2024-05-01" in result.output

    args = mock_gh.call_args[0][0]
    assert "chezmoi dotfiles" in args
    assert "--limit" in args and "3" in args


def test_search_passes_language_and_stars_filters() -> None:
    runner = CliRunner()

    with patch("research.scout.search._run_gh", return_value=_gh_result(json.dumps([]))) as mock_gh:
        runner.invoke(
            root_cli,
            ["scout", "search", "query", "--language", "Go", "--stars", "100"],
        )

    args = mock_gh.call_args[0][0]
    assert "--language" in args
    assert "Go" in args
    assert "--stars" in args
    assert ">=100" in args


def test_search_with_forks_shows_top_forks_sorted_by_stars() -> None:
    runner = CliRunner()
    repos = [_repo(full_name="owner/repo")]
    forks = [
        {"full_name": "alice/repo", "stargazers_count": 42, "pushed_at": "2024-06-01T00:00:00Z"},
        {"full_name": "bob/repo", "stargazers_count": 10, "pushed_at": "2024-01-01T00:00:00Z"},
    ]

    with (
        patch("research.scout.search._run_gh", return_value=_gh_result(json.dumps(repos))),
        patch("research.scout.search.api", return_value=forks) as mock_api,
    ):
        result = runner.invoke(
            root_cli, ["scout", "search", "query", "--limit", "3", "--forks", "5"]
        )

    assert result.exit_code == 0
    assert "top forks:" in result.output
    assert "alice/repo (stars: 42, last commit: 2024-06-01)" in result.output
    assert "bob/repo (stars: 10, last commit: 2024-01-01)" in result.output

    endpoint = mock_api.call_args[0][0]
    assert endpoint == "repos/owner/repo/forks"
    assert mock_api.call_args.kwargs["params"]["per_page"] == "5"


def test_search_skips_forks_when_option_not_given() -> None:
    runner = CliRunner()
    repos = [_repo()]

    with (
        patch("research.scout.search._run_gh", return_value=_gh_result(json.dumps(repos))),
        patch("research.scout.search.api") as mock_api,
    ):
        result = runner.invoke(root_cli, ["scout", "search", "query"])

    assert result.exit_code == 0
    assert "top forks:" not in result.output
    mock_api.assert_not_called()


def test_search_no_results() -> None:
    runner = CliRunner()

    with patch("research.scout.search._run_gh", return_value=_gh_result(json.dumps([]))):
        result = runner.invoke(root_cli, ["scout", "search", "nonexistent-query"])

    assert result.exit_code == 0
    assert "No repositories found" in result.output


def test_search_handles_gh_failure() -> None:
    runner = CliRunner()

    with patch(
        "research.scout.search._run_gh",
        return_value=_gh_result(stderr="rate limit exceeded", returncode=1),
    ):
        result = runner.invoke(root_cli, ["scout", "search", "query"])

    assert result.exit_code != 0
    assert "rate limit exceeded" in result.output


def test_search_handles_fork_fetch_failure() -> None:
    runner = CliRunner()
    repos = [_repo(full_name="owner/repo")]

    with (
        patch("research.scout.search._run_gh", return_value=_gh_result(json.dumps(repos))),
        patch("research.scout.search.api", side_effect=APIError("not found")),
    ):
        result = runner.invoke(root_cli, ["scout", "search", "query", "--forks", "3"])

    assert result.exit_code == 0
    assert "forks: failed to fetch" in result.output
