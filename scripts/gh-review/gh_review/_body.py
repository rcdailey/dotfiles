"""Shared Click option for Markdown bodies."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

import click


def body_option(*, required: bool) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Add a body option that can read literal Markdown from stdin."""
    return click.option(
        "--body",
        required=required,
        default=None,
        help="body text, or - to read from stdin",
    )


def read_body(body: str | None) -> str | None:
    """Read a body from stdin when requested."""
    if body != "-":
        return body
    return sys.stdin.read()
