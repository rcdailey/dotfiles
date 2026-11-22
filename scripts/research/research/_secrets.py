"""API key lookup from the environment or the rbw (Bitwarden) vault."""

from __future__ import annotations

import os
import subprocess


class SecretError(Exception):
    """An API key could not be read."""


def read_secret(env_var: str, rbw_item: str) -> str:
    """Return the key from `env_var`, else from the rbw item of that name.

    Concurrent invocations share one unlock prompt: the serializing pinentry
    wrapper cancels the queued prompts once the vault is open, so a cancelled
    first attempt is retried once against the now-unlocked agent.
    """
    key = os.environ.get(env_var)
    if key:
        return key
    try:
        result = _rbw_get(rbw_item)
    except FileNotFoundError:
        raise SecretError(f"{env_var} not set and `rbw` binary not found") from None
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or f"rbw exited {e.returncode}"
        raise SecretError(f"failed to read {rbw_item} from rbw: {msg}") from e
    key = result.stdout.strip()
    if not key:
        raise SecretError(f"rbw returned empty value for {rbw_item}")
    return key


def _rbw_get(item: str) -> subprocess.CompletedProcess[str]:
    cmd = ["rbw", "get", item]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        if "pinentry cancelled" not in e.stderr:
            raise
    return subprocess.run(cmd, capture_output=True, text=True, check=True)
