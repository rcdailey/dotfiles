"""GraphQL client for the Linear API."""

from __future__ import annotations

import json
import os
import re
import time

import click

from linear_cli import _auth, _http
from linear_cli._config import LINEAR_BASE_URL
from linear_cli._errors import LinearError, die

_RATE_LIMIT_WARN_THRESHOLD = 100
_MAX_QUERY_ATTEMPTS = 2


def _is_mutation(query: str) -> bool:
    """Return whether a GraphQL document contains a mutation operation."""
    return re.search(r"\bmutation\b", query, re.IGNORECASE) is not None


def _retry_delay(response: _http.Response | None, attempt: int) -> float:
    """Return a bounded retry delay, honoring integer Retry-After values."""
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), 5.0)
    return 0.5 * (attempt + 1)


def _send(body: bytes, headers: dict, *, retry: bool) -> _http.Response:
    """Send one GraphQL request with bounded retries for safe operations."""
    attempts = _MAX_QUERY_ATTEMPTS if retry else 1
    for attempt in range(attempts):
        try:
            response = _http.post(LINEAR_BASE_URL, body, headers)
        except _http.TRANSPORT_ERRORS as exc:
            if attempt + 1 < attempts:
                time.sleep(_retry_delay(None, attempt))
                continue
            raise LinearError(f"Linear API request failed: {exc}") from exc

        transient = response.status == 429 or response.status >= 500
        if transient and attempt + 1 < attempts:
            time.sleep(_retry_delay(response, attempt))
            continue
        return response

    raise LinearError("Linear API request failed")


def _response_body(response: _http.Response) -> dict:
    """Decode and validate a GraphQL response body."""
    try:
        body = response.json()
    except ValueError as exc:
        raise LinearError("Linear API returned invalid JSON") from exc
    if not isinstance(body, dict):
        raise LinearError("Linear API returned an invalid response")
    return body


def _graphql_errors(body: dict) -> list:
    """Return the response's GraphQL errors list."""
    errors = body.get("errors") or []
    if not isinstance(errors, list):
        raise LinearError("Linear API returned an invalid response")
    return errors


def _error_message(errors: list) -> str:
    """Join GraphQL error messages into one line."""
    return "; ".join(
        error.get("message", str(error)) if isinstance(error, dict) else str(error)
        for error in errors
    )


def _get_auth_header() -> dict:
    """Return Authorization header dict based on available credentials.

    Priority: LINEAR_API_KEY env var > OAuth access token > stored API key.
    Dies with a clear message if none are available.
    """
    api_key = os.environ.get("LINEAR_API_KEY")
    if api_key:
        return {"Authorization": api_key}
    tokens = _auth.load_tokens()
    if tokens and tokens.get("auth_type") == "api_key" and tokens.get("api_key"):
        return {"Authorization": tokens["api_key"]}
    token = _auth.get_access_token(tokens)
    if token:
        return {"Authorization": f"Bearer {token}"}
    die("not authenticated; run 'linear auth login' or set LINEAR_API_KEY")


def _warn_rate_limit(response: _http.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is None:
        return
    try:
        if int(remaining) >= _RATE_LIMIT_WARN_THRESHOLD:
            return
    except ValueError:
        return
    reset = response.headers.get("X-RateLimit-Reset", "unknown")
    click.echo(f"warning: rate limit low ({remaining} remaining, resets {reset})", err=True)


def _request(query: str, variables: dict | None) -> dict:
    """Send a GraphQL document and return the decoded body; HTTP failures raise LinearError.

    Retries once on 401 by refreshing the OAuth token.
    """
    headers = {**_get_auth_header(), "Content-Type": "application/json"}
    payload: dict = {"query": query}
    if variables:
        payload["variables"] = variables
    body = json.dumps(payload).encode()

    retry = not _is_mutation(query)
    response = _send(body, headers, retry=retry)

    # Refresh only when the request used the stored OAuth token; retrying an API-key request with
    # it would silently switch workspaces.
    if response.status == 401 and headers["Authorization"].startswith("Bearer "):
        tokens = _auth.load_tokens()
        if tokens and tokens.get("auth_type") != "api_key":
            try:
                new_tokens = _auth.refresh_access_token(tokens)
            except Exception as exc:
                raise LinearError("OAuth refresh failed; run 'linear auth login'") from exc
            headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
            response = _send(body, headers, retry=retry)

    if response.status >= 400:
        try:
            errors = _graphql_errors(_response_body(response))
        except LinearError:
            errors = []
        if errors:
            raise LinearError(_error_message(errors))
        raise LinearError(f"Linear API returned HTTP {response.status}")

    _warn_rate_limit(response)
    return _response_body(response)


def _data(body: dict) -> dict:
    data = body.get("data") or {}
    if not isinstance(data, dict):
        raise LinearError("Linear API returned an invalid response")
    return data


def execute(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL document and return its ``data``; any GraphQL error raises LinearError."""
    body = _request(query, variables)
    errors = _graphql_errors(body)
    if errors:
        raise LinearError(_error_message(errors))
    return _data(body)


def paginate(
    query: str,
    variables: dict | None,
    connection_path: list[str],
    *,
    limit: int | None = None,
    first_page: dict | None = None,
) -> list:
    """Follow Relay cursor pagination and accumulate all nodes.

    ``connection_path`` is the list of keys to reach the connection object
    (which has ``pageInfo`` and ``nodes``) from the ``data`` dict root.
    Example: ["issues"] or ["team", "issues"]. ``first_page`` is an already fetched
    connection, typically embedded in a combined request; fetching resumes after it.
    """
    variables = dict(variables or {})
    nodes: list = []
    connection = first_page

    while True:
        if connection is None:
            if limit is not None:
                remaining = limit - len(nodes)
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
        connection = None

    return nodes[:limit] if limit is not None else nodes
