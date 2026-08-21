"""Persistent per-session tool failure ledger."""

from __future__ import annotations

import contextlib
import shlex
import sys
from collections.abc import Callable
from typing import Any, TextIO

_ERRORS_KEY = "errors"
_EXPIRY_SECONDS = 24 * 3600


def _session_key() -> str | None:
    from research._cache import get_session_id

    session_id = get_session_id()
    return f"research:{session_id}:{_ERRORS_KEY}" if session_id else None


def record_error(arguments: list[str], message: str) -> None:
    """Append one failed invocation to the active session ledger."""
    from research._cache import get_cache

    key = _session_key()
    if key is None:
        return
    command = shlex.join(["research", *arguments])
    entry = f"Tool: research\nInput: {command}\nError:\n{message.strip()}"
    cache = get_cache()
    with cache.transact():
        entries = list(cache.get(key, []))
        entries.append(entry)
        cache.set(key, entries, expire=_EXPIRY_SECONDS)


def get_errors() -> list[str]:
    """Return all failures recorded for the active session."""
    from research._cache import get_cache

    key = _session_key()
    if key is None:
        return []
    return list(get_cache().get(key, []))


class _TeeStream:
    def __init__(self, target: TextIO, recorder: TextIO) -> None:
        self._target = target
        self._recorder = recorder

    def write(self, text: str) -> int:
        self._target.write(text)
        return self._recorder.write(text)

    def flush(self) -> None:
        self._target.flush()
        self._recorder.flush()

    def isatty(self) -> bool:
        return self._target.isatty()


def run_with_error_ledger(command: Callable[[], Any]) -> None:
    """Run the root CLI and persist its output when the invocation fails."""
    from io import StringIO

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    recorder = StringIO()
    sys.stdout = _TeeStream(original_stdout, recorder)
    sys.stderr = _TeeStream(original_stderr, recorder)
    try:
        command()
    except SystemExit as error:
        if error.code not in (None, 0):
            message = recorder.getvalue() or f"command exited with status {error.code}"
            _record_safely(sys.argv[1:], message)
        raise
    except BaseException as error:
        message = recorder.getvalue()
        detail = f"{type(error).__name__}: {error}"
        _record_safely(sys.argv[1:], f"{message}{detail}")
        raise
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def _record_safely(arguments: list[str], message: str) -> None:
    """Never replace the original command failure with a ledger failure."""
    with contextlib.suppress(Exception):
        record_error(arguments, message)
