"""Configuration from environment."""

from __future__ import annotations

import os

from linear_cli._errors import die

LINEAR_BASE_URL = os.environ.get("LINEAR_BASE_URL", "https://api.linear.app/graphql")


def require_env(name: str) -> str:
    """Return env var value or die with clear message."""
    value = os.environ.get(name)
    if not value:
        die(f"{name} is not set")
    return value


def get_api_key() -> str | None:
    """Return LINEAR_API_KEY env var value, or None if not set."""
    value = os.environ.get("LINEAR_API_KEY")
    return value if value else None


def get_client_id() -> str | None:
    """Return LINEAR_CLIENT_ID env var value, or None if not set."""
    value = os.environ.get("LINEAR_CLIENT_ID")
    return value if value else None
