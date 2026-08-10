"""httpx-based GraphQL client for the Linear API."""

from __future__ import annotations

import atexit
import os
import re
import time

import click
import httpx

from linear_cli import _auth
from linear_cli._config import LINEAR_BASE_URL
from linear_cli._errors import LinearError, die

_RATE_LIMIT_WARN_THRESHOLD = 100
_TIMEOUT = httpx.Timeout(10.0, connect=15.0)
_MAX_QUERY_ATTEMPTS = 2
_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    """Return the process-wide HTTP client."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=_TIMEOUT)
        atexit.register(_client.close)
    return _client


def _is_mutation(query: str) -> bool:
    """Return whether a GraphQL document contains a mutation operation."""
    return re.search(r"\bmutation\b", query, re.IGNORECASE) is not None


def _retry_delay(response: httpx.Response | None, attempt: int) -> float:
    """Return a bounded retry delay, honoring integer Retry-After values."""
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), 5.0)
    return 0.5 * (attempt + 1)


def _send(payload: dict, headers: dict, *, retry: bool) -> httpx.Response:
    """Send one GraphQL request with bounded retries for safe operations."""
    attempts = _MAX_QUERY_ATTEMPTS if retry else 1
    for attempt in range(attempts):
        try:
            response = _get_client().post(
                LINEAR_BASE_URL,
                json=payload,
                headers=headers,
            )
        except httpx.RequestError as exc:
            if attempt + 1 < attempts:
                time.sleep(_retry_delay(None, attempt))
                continue
            raise LinearError(f"Linear API request failed: {exc}") from exc

        transient = response.status_code == 429 or response.status_code >= 500
        if transient and attempt + 1 < attempts:
            time.sleep(_retry_delay(response, attempt))
            continue
        return response

    raise LinearError("Linear API request failed")


def _response_body(response: httpx.Response) -> dict:
    """Decode and validate a GraphQL response body."""
    try:
        body = response.json()
    except ValueError as exc:
        raise LinearError("Linear API returned invalid JSON") from exc
    if not isinstance(body, dict):
        raise LinearError("Linear API returned an invalid response")
    return body


def _raise_graphql_errors(body: dict) -> None:
    """Raise one LinearError for a present GraphQL errors field."""
    if "errors" not in body:
        return
    errors = body["errors"]
    if not isinstance(errors, list):
        raise LinearError("Linear API returned an invalid response")
    if not errors:
        return
    messages = "; ".join(
        error.get("message", str(error)) if isinstance(error, dict) else str(error)
        for error in errors
    )
    raise LinearError(messages)


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

    retry = not _is_mutation(query)
    response = _send(payload, headers, retry=retry)

    if response.status_code == 401:
        tokens = _auth.load_tokens()
        if tokens:
            try:
                new_tokens = _auth.refresh_access_token(tokens)
                headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                response = _send(payload, headers, retry=retry)
            except Exception as exc:
                raise LinearError("OAuth refresh failed; run 'linear auth login'") from exc

    if response.status_code >= 400:
        try:
            body = _response_body(response)
        except LinearError:
            body = None
        if body is not None:
            _raise_graphql_errors(body)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LinearError(f"Linear API returned HTTP {response.status_code}") from exc

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

    body = _response_body(response)
    _raise_graphql_errors(body)
    data = body.get("data", {})
    if not isinstance(data, dict):
        raise LinearError("Linear API returned an invalid response")
    return data


def paginate(
    query: str,
    variables: dict | None,
    connection_path: list[str],
    *,
    limit: int | None = None,
) -> list:
    """Follow Relay cursor pagination and accumulate all nodes.

    ``connection_path`` is the list of keys to reach the connection object
    (which has ``pageInfo`` and ``nodes``) from the ``data`` dict root.
    Example: ["issues"] or ["team", "issues"].
    """
    variables = dict(variables or {})
    nodes: list = []

    while True:
        if limit is not None:
            remaining = limit - len(nodes)
            if remaining <= 0:
                break
            variables["first"] = min(variables.get("first") or remaining, remaining)
        data = execute(query, variables)
        connection = data
        for key in connection_path:
            connection = connection[key]

        nodes.extend(connection.get("nodes", []))

        if limit is not None and len(nodes) >= limit:
            break

        page_info = connection.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        variables["after"] = page_info["endCursor"]

    return nodes[:limit] if limit is not None else nodes
