"""httpx-based GraphQL client for the Linear API."""

from __future__ import annotations

import os

import click
import httpx

from linear_cli import _auth
from linear_cli._config import LINEAR_BASE_URL
from linear_cli._errors import LinearError, die

_RATE_LIMIT_WARN_THRESHOLD = 100


def _get_auth_header() -> dict:
    """Return Authorization header dict based on available credentials.

    Priority: LINEAR_API_KEY env var > OAuth access token > stored API key.
    Dies with a clear message if none are available.
    """
    api_key = os.environ.get("LINEAR_API_KEY")
    if api_key:
        return {"Authorization": api_key}
    token = _auth.get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    stored_key = _auth.get_stored_api_key()
    if stored_key:
        return {"Authorization": stored_key}
    die("not authenticated; run 'linear auth login' or set LINEAR_API_KEY")


def execute(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against the Linear API.

    Returns the ``data`` dict from the response. Raises LinearError if the
    response contains GraphQL errors. Retries once on 401 by refreshing
    the OAuth token.
    """
    headers = {
        **_get_auth_header(),
        "Content-Type": "application/json",
    }
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables

    response = httpx.post(LINEAR_BASE_URL, json=payload, headers=headers)

    if response.status_code == 401:
        tokens = _auth.load_tokens()
        if tokens:
            try:
                new_tokens = _auth.refresh_access_token(tokens)
                headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                response = httpx.post(LINEAR_BASE_URL, json=payload, headers=headers)
            except Exception:
                pass

    if response.status_code >= 400:
        try:
            body = response.json()
            errors = body.get("errors", [])
            if errors:
                messages = "; ".join(e.get("message", str(e)) for e in errors)
                raise LinearError(messages)
        except (ValueError, LinearError):
            raise
        except Exception:
            pass
        response.raise_for_status()

    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        try:
            if int(remaining) < _RATE_LIMIT_WARN_THRESHOLD:
                reset = response.headers.get("X-RateLimit-Reset", "unknown")
                click.echo(
                    f"warning: rate limit low ({remaining} remaining, resets {reset})",
                    err=True,
                )
        except ValueError:
            pass

    body = response.json()
    errors = body.get("errors")
    if errors:
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        raise LinearError(messages)

    return body.get("data", {})


def paginate(query: str, variables: dict | None, connection_path: list[str]) -> list:
    """Follow Relay cursor pagination and accumulate all nodes.

    ``connection_path`` is the list of keys to reach the connection object
    (which has ``pageInfo`` and ``nodes``) from the ``data`` dict root.
    Example: ["issues"] or ["team", "issues"].
    """
    variables = dict(variables or {})
    nodes: list = []

    while True:
        data = execute(query, variables)
        connection = data
        for key in connection_path:
            connection = connection[key]

        nodes.extend(connection.get("nodes", []))

        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        variables["after"] = page_info["endCursor"]

    return nodes
