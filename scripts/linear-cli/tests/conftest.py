"""Shared test fixtures."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolate_auth(monkeypatch, tmp_path):
    """Set LINEAR_API_KEY and isolate token storage for every test.

    Tests that need unauthenticated behavior can call
    ``monkeypatch.delenv("LINEAR_API_KEY", raising=False)`` to unset the key.
    Token storage is redirected to a per-test temp directory so real stored
    tokens are never read or written during tests.
    """
    monkeypatch.setenv("LINEAR_API_KEY", "test-key")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))


@pytest.fixture
def mock_execute():
    """Patch _graphql.execute at the module level for all callers."""
    with patch("linear_cli._graphql.execute") as mock:
        yield mock
