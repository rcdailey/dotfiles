"""Tests for _auth PKCE helpers, token storage, and _graphql auth header."""

from __future__ import annotations

import base64
import hashlib
import time
from unittest.mock import patch

import pytest

from click.testing import CliRunner

from linear_cli._auth import (
    _generate_challenge,
    _generate_verifier,
    get_access_token,
    get_stored_api_key,
    load_tokens,
    save_api_key,
    save_tokens,
)
from linear_cli._graphql import _get_auth_header
from linear_cli.cli import cli

_VERIFIER_CHARSET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")


def test_pkce_verifier_length_and_chars():
    v = _generate_verifier()
    assert 43 <= len(v) <= 128
    assert all(c in _VERIFIER_CHARSET for c in v)


def test_pkce_challenge_s256():
    verifier = "test-verifier-string"
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    assert _generate_challenge(verifier) == expected


def test_load_tokens_returns_none_when_missing():
    # autouse isolate_auth fixture redirects XDG_STATE_HOME to a clean tmp_path
    assert load_tokens() is None


def test_save_and_load_tokens_roundtrip():
    data = {
        "access_token": "tok123",
        "refresh_token": "ref456",
        "expires_at": time.time() + 3600,
        "client_id": "client-abc",
    }
    save_tokens(data)
    loaded = load_tokens()
    assert loaded is not None
    assert loaded["access_token"] == "tok123"
    assert loaded["refresh_token"] == "ref456"
    assert loaded["client_id"] == "client-abc"


def test_get_access_token_returns_none_when_no_tokens():
    assert get_access_token() is None


def test_get_auth_header_prefers_api_key(monkeypatch):
    monkeypatch.setenv("LINEAR_API_KEY", "my-api-key")
    header = _get_auth_header()
    assert header == {"Authorization": "my-api-key"}


def test_get_auth_header_falls_back_to_oauth(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli._auth.get_access_token", return_value="oauth-tok"):
        header = _get_auth_header()
    assert header == {"Authorization": "Bearer oauth-tok"}


def test_get_auth_header_falls_back_to_stored_api_key(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli._auth.get_access_token", return_value=None):
        with patch("linear_cli._auth.get_stored_api_key", return_value="stored-key"):
            header = _get_auth_header()
    assert header == {"Authorization": "stored-key"}


def test_get_auth_header_prefers_oauth_over_stored_api_key(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli._auth.get_access_token", return_value="oauth-tok"):
        with patch("linear_cli._auth.get_stored_api_key", return_value="stored-key"):
            header = _get_auth_header()
    assert header == {"Authorization": "Bearer oauth-tok"}


def test_get_auth_header_dies_when_neither(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli._auth.get_access_token", return_value=None):
        with patch("linear_cli._auth.get_stored_api_key", return_value=None):
            with pytest.raises(SystemExit):
                _get_auth_header()


def test_save_and_load_api_key_roundtrip():
    save_api_key("lin_api_testkey123")
    key = get_stored_api_key()
    assert key == "lin_api_testkey123"


def test_get_stored_api_key_ignores_oauth_tokens():
    save_tokens(
        {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999, "auth_type": "oauth"}
    )
    assert get_stored_api_key() is None


def test_get_access_token_ignores_api_key_tokens():
    save_api_key("lin_api_testkey123")
    assert get_access_token() is None


def test_auth_status_not_authenticated(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    result = CliRunner().invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "not authenticated" in result.output


def test_auth_status_api_key(monkeypatch):
    monkeypatch.setenv("LINEAR_API_KEY", "my-key")
    result = CliRunner().invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "API key" in result.output


def test_auth_logout(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    save_tokens(
        {"access_token": "tok", "refresh_token": "ref", "expires_at": 9999, "client_id": "c"}
    )
    result = CliRunner().invoke(cli, ["auth", "logout"])
    assert result.exit_code == 0
    assert "Logged out" in result.output
    assert load_tokens() is None


def test_auth_help_shows_subcommands():
    result = CliRunner().invoke(cli, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output
    assert "logout" in result.output
    assert "status" in result.output


def test_login_help_shows_oauth_and_api_key_flags():
    result = CliRunner().invoke(cli, ["auth", "login", "--help"])
    assert result.exit_code == 0
    assert "--oauth" in result.output
    assert "--api-key" in result.output


def test_login_prompts_for_api_key_when_no_client_id(monkeypatch):
    monkeypatch.delenv("LINEAR_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli.auth._validate_api_key", return_value="user@example.com"):
        result = CliRunner().invoke(cli, ["auth", "login"], input="lin_api_testkey\n")
    assert result.exit_code == 0
    assert "Authenticated as user@example.com" in result.output
    assert get_stored_api_key() == "lin_api_testkey"


def test_login_api_key_flag_forces_prompt(monkeypatch):
    monkeypatch.setenv("LINEAR_CLIENT_ID", "some-client-id")
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli.auth._validate_api_key", return_value="user@example.com"):
        result = CliRunner().invoke(cli, ["auth", "login", "--api-key"], input="lin_api_testkey\n")
    assert result.exit_code == 0
    assert "Authenticated as user@example.com" in result.output


def test_login_api_key_dies_on_invalid_key(monkeypatch):
    monkeypatch.delenv("LINEAR_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    with patch("linear_cli.auth._validate_api_key", return_value=None):
        result = CliRunner().invoke(cli, ["auth", "login"], input="bad-key\n")
    assert result.exit_code != 0


def test_login_oauth_flag_dies_without_client_id(monkeypatch):
    monkeypatch.delenv("LINEAR_CLIENT_ID", raising=False)
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    result = CliRunner().invoke(cli, ["auth", "login", "--oauth"])
    assert result.exit_code != 0


def test_auth_status_shows_stored_api_key(monkeypatch):
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    save_api_key("lin_api_testkey")
    result = CliRunner().invoke(cli, ["auth", "status"])
    assert result.exit_code == 0
    assert "stored API key" in result.output
