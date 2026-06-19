"""Authentication commands: login, logout, status."""

from __future__ import annotations

import os
import time

import click
import httpx

from linear_cli._auth import (
    clear_tokens,
    load_tokens,
    run_oauth_flow,
    save_api_key,
)
from linear_cli._click import HelpfulGroup
from linear_cli._config import LINEAR_BASE_URL, get_client_id
from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute
from linear_cli._queries import VIEWER_QUERY


def _validate_api_key(key: str) -> str | None:
    """Call viewer query with key. Returns email on success, None on failure."""
    try:
        response = httpx.post(
            LINEAR_BASE_URL,
            json={"query": VIEWER_QUERY},
            headers={"Authorization": key, "Content-Type": "application/json"},
        )
        response.raise_for_status()
        body = response.json()
        return body.get("data", {}).get("viewer", {}).get("email")
    except Exception:
        return None


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Manage Linear authentication."""


@cli.command()
@click.option("--port", default=9876, show_default=True, help="Local port for OAuth callback.")
@click.option("--oauth", "force_oauth", is_flag=True, help="Force OAuth flow.")
@click.option("--api-key", "force_api_key", is_flag=True, help="Authenticate with an API key.")
def login(port: int, force_oauth: bool, force_api_key: bool) -> None:
    """Authenticate via OAuth2 PKCE or API key."""
    use_oauth = force_oauth or (not force_api_key and bool(get_client_id()))

    if use_oauth:
        client_id = get_client_id()
        if not client_id:
            die("LINEAR_CLIENT_ID is not set; cannot use OAuth")
        run_oauth_flow(client_id, port)
        try:
            data = execute(VIEWER_QUERY)
            email = data.get("viewer", {}).get("email", "unknown")
            click.echo(f"Authenticated as {email}")
        except LinearError:
            click.echo("Authenticated successfully.")
    else:
        key = click.prompt("Linear API key", hide_input=True)
        email = _validate_api_key(key)
        if email is None:
            die("API key validation failed; check the key and try again")
        save_api_key(key)
        click.echo(f"Authenticated as {email}")


@cli.command()
def logout() -> None:
    """Clear stored credentials."""
    clear_tokens()
    click.echo("Logged out.")


@cli.command()
def status() -> None:
    """Show current authentication status."""
    api_key = os.environ.get("LINEAR_API_KEY")
    if api_key:
        click.echo("authenticated via API key (LINEAR_API_KEY)")
        return

    tokens = load_tokens()
    if tokens:
        auth_type = tokens.get("auth_type")
        if auth_type == "api_key":
            click.echo("authenticated via stored API key")
            return
        if tokens.get("access_token"):
            expires_at = tokens.get("expires_at", 0)
            remaining = int(expires_at - time.time())
            if remaining > 0:
                hours = remaining // 3600
                click.echo(f"authenticated via OAuth token (expires in ~{hours}h)")
            else:
                click.echo("OAuth token expired; run 'linear auth login' to re-authenticate")
            return

    click.echo("not authenticated; run 'linear auth login' or set LINEAR_API_KEY")
