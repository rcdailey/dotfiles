"""Shared test fixtures."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_check_deps():
    """Prevent actual gh CLI calls during tests."""
    with patch("gh_review.cli.check_deps"):
        yield
