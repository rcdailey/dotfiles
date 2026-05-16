"""Tests for the status subcommand."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from research.cli import cli


def test_status_shows_budget() -> None:
    mock_cache = MagicMock()
    mock_cache.get.return_value = 0
    mock_cache.__iter__ = MagicMock(return_value=iter([]))

    runner = CliRunner()
    with patch("research._cache.get_cache", return_value=mock_cache):
        result = runner.invoke(cli, ["status"], env={"RESEARCH_SESSION_ID": "test-session"})

    assert result.exit_code == 0
    assert "calls used" in result.output
