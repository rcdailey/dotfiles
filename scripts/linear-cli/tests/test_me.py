"""Tests for the me command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _viewer_data() -> dict:
    return {
        "viewer": {
            "id": "user-123",
            "name": "Alice Smith",
            "displayName": "alice",
            "email": "alice@example.com",
            "active": True,
        }
    }


def test_me_shows_user_info():
    with patch("linear_cli.me.execute", return_value=_viewer_data()):
        result = CliRunner().invoke(cli, ["me"])

    assert result.exit_code == 0
    assert "alice@example.com" in result.output
    assert "Alice Smith" in result.output
    assert "user-123" in result.output


def test_me_missing_api_key_exits_with_error(monkeypatch):
    """me exits with a clear error when LINEAR_API_KEY is not set and no OAuth tokens exist."""
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(cli, ["me"])
    assert result.exit_code != 0
    assert "linear auth login" in result.output
