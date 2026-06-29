"""Error types and fatal exit helper."""

from __future__ import annotations

import sys
from typing import NoReturn


class GhError(Exception):
    """GitHub CLI operation failure."""

    def __init__(self, message: str, *, status: int = 0) -> None:
        super().__init__(message)
        self.status = status


def die(message: str) -> NoReturn:
    """Print error to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)
