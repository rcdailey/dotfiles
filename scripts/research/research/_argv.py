"""Normalize recurrent CLI argument mistakes."""

from __future__ import annotations


def normalize_arguments(arguments: list[str]) -> list[str]:
    """Translate a result-count shorthand into the canonical search options."""
    if arguments[:2] != ["web", "search"]:
        return arguments

    normalized: list[str] = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        normalized.append(argument)
        if argument == "--results" and _next_is_integer(arguments, index):
            normalized.extend(["--max-results", arguments[index + 1]])
            index += 1
        index += 1
    return normalized


def _next_is_integer(arguments: list[str], index: int) -> bool:
    """Return whether the next argument is an unsigned integer."""
    return index + 1 < len(arguments) and arguments[index + 1].isdigit()
