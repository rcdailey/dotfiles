"""Acceptance snapshot errors."""

from __future__ import annotations

import sys
from typing import NoReturn


class SnapshotError(Exception):
    """A snapshot operation could not be completed safely."""


def die(message: str) -> NoReturn:
    """Print an error and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)
