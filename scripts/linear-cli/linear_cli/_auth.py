"""OAuth2 PKCE helpers and token storage for Linear authentication."""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

import click
import httpx

from linear_cli._errors import die

_LINEAR_TOKEN_URL = "https://api.linear.app/oauth/token"
_LINEAR_AUTH_URL = "https://linear.app/oauth/authorize"
_OAUTH_TIMEOUT = 120
_HTML_SUCCESS = b"""<!DOCTYPE html>
<html><body><p>Authentication successful. You can close this tab.</p></body></html>"""


def _get_tokens_path() -> Path:
    """Return path to tokens file, respecting XDG_STATE_HOME."""
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "linear-cli" / "tokens.json"


def _generate_verifier() -> str:
    """Generate a PKCE code verifier (RFC 7636): 43-128 URL-safe random chars."""
    return secrets.token_urlsafe(64)


def _generate_challenge(verifier: str) -> str:
    """Return S256 PKCE code challenge from verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def load_tokens() -> dict | None:
    """Read tokens from storage. Returns None if missing or malformed."""
    path = _get_tokens_path()
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            return None
        return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_tokens(data: dict) -> None:
    """Write tokens to storage with secure permissions (dirs 700, file 600)."""
    path = _get_tokens_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(data))
    path.chmod(0o600)


def clear_tokens() -> None:
    """Delete stored tokens file."""
    path = _get_tokens_path()
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def refresh_access_token(tokens: dict) -> dict:
    """Exchange refresh token for new tokens. Saves and returns updated tokens."""
    client_id = tokens.get("client_id", "")
    response = httpx.post(
        _LINEAR_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": client_id,
        },
    )
    response.raise_for_status()
    new_data = response.json()
    updated: dict = {
        "access_token": new_data["access_token"],
        "refresh_token": new_data.get("refresh_token", tokens["refresh_token"]),
        "expires_at": time.time() + new_data.get("expires_in", 86399),
        "client_id": client_id,
        "auth_type": "oauth",
    }
    save_tokens(updated)
    return updated


def get_access_token() -> str | None:
    """Return a valid OAuth access token, refreshing if within 5-min expiry buffer.

    Returns None if no tokens are stored, tokens are API key type, or refresh fails.
    """
    tokens = load_tokens()
    if not tokens:
        return None
    if tokens.get("auth_type") == "api_key":
        return None
    expires_at = tokens.get("expires_at", 0)
    if time.time() >= expires_at - 300:
        try:
            tokens = refresh_access_token(tokens)
        except Exception:
            return None
    return tokens.get("access_token")


def get_stored_api_key() -> str | None:
    """Return stored API key if tokens file contains one, else None."""
    tokens = load_tokens()
    if tokens and tokens.get("auth_type") == "api_key":
        return tokens.get("api_key") or None
    return None


def save_api_key(key: str) -> None:
    """Persist an API key to token storage."""
    save_tokens({"api_key": key, "auth_type": "api_key"})


def run_oauth_flow(client_id: str, port: int) -> dict:
    """Run full OAuth2 PKCE flow: open browser, capture callback, exchange code.

    Returns stored tokens dict.
    """
    verifier = _generate_verifier()
    challenge = _generate_challenge(verifier)
    state = secrets.token_urlsafe(16)
    redirect_uri = f"http://localhost:{port}/callback"

    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "read,write",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    auth_url = f"{_LINEAR_AUTH_URL}?{params}"

    captured: dict[str, str | None] = {}
    event = threading.Event()

    class _CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            captured["code"] = (qs.get("code") or [None])[0]
            captured["state"] = (qs.get("state") or [None])[0]
            captured["error"] = (qs.get("error") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_HTML_SUCCESS)))
            self.end_headers()
            self.wfile.write(_HTML_SUCCESS)
            event.set()

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            pass

    server = http.server.HTTPServer(("localhost", port), _CallbackHandler)
    server.timeout = 1

    def _serve() -> None:
        start = time.time()
        while not event.is_set() and (time.time() - start) < _OAUTH_TIMEOUT:
            server.handle_request()
        server.server_close()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()

    click.echo(f"Opening browser for authentication on port {port}...")
    webbrowser.open(auth_url)

    if not event.wait(timeout=_OAUTH_TIMEOUT + 2):
        die("timeout waiting for OAuth callback")

    thread.join(timeout=2)

    if captured.get("error"):
        die(f"OAuth error: {captured['error']}")
    if captured.get("state") != state:
        die("OAuth state mismatch; possible CSRF attack")

    code = captured.get("code")
    if not code:
        die("no authorization code received")

    response = httpx.post(
        _LINEAR_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": verifier,
        },
    )
    response.raise_for_status()
    token_data = response.json()

    tokens: dict = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "expires_at": time.time() + token_data.get("expires_in", 86399),
        "client_id": client_id,
        "auth_type": "oauth",
    }
    save_tokens(tokens)
    return tokens
