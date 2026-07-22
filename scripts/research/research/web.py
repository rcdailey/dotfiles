"""Web search and fetch subcommand."""

from __future__ import annotations

import subprocess
import sys

import click

from research._budget import budget_refund, budget_reserve
from research._cache import get_cache, read_cached_content, write_cached_content
from research._fetch import FetchError, fetch_markdown
from research._linkup import SearchError, format_search_results
from research._render import (
    DEFAULT_MAX_CHARS,
    is_github_url,
    is_pdf_url,
    reroute_message,
    strip_github_host,
    truncate_output,
)

DEFAULT_MAX_RESULTS = 5


@click.group(invoke_without_command=False)
def cli() -> None:
    """Web search and page fetching via Linkup."""


@cli.command(name="search")
@click.argument("query")
@click.option("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
def search_cmd(query: str, max_results: int) -> None:
    """Search the web via Linkup."""
    cache = get_cache()
    budget_reserve(cache, None)

    try:
        from research._linkup import search

        results = search(query, max_results)
        click.echo(format_search_results(results))
    except SearchError as e:
        budget_refund(cache)
        click.echo(f"error: {e}", err=True)
        sys.exit(1)


@cli.command(name="fetch")
@click.argument("url")
@click.option("--find", help="show only paragraphs matching this pattern")
@click.option("-C", "--context", type=int, default=0, help="paragraphs of context around matches")
@click.option("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
def fetch_cmd(url: str, find: str | None, context: int, max_chars: int) -> None:
    """Fetch a URL as clean markdown."""
    # Check for reroutes before burning budget
    if is_github_url(url):
        path = strip_github_host(url)
        parts = path.split("/")

        # Skip non-repo paths; let them fall through to normal web fetch
        if len(parts) >= 2 and parts[0] not in ("orgs", "topics", "settings", "features"):
            owner, repo_name = parts[0], parts[1]

            if len(parts) >= 4 and parts[2] == "discussions" and parts[3].isdigit():
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                number = int(parts[3])
                reroute_message(
                    url,
                    f"scout discussion {owner}/{repo_name} {number}",
                    "github.com discussion",
                )
                from research._ghapi import APIError, view_discussion
                from research._render import format_issue_body
                from research.scout.issues import _render_comments

                try:
                    data = view_discussion(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                category = data.get("category", {}).get("name", "")
                cat_str = f" [{category}]" if category else ""
                click.echo(
                    format_issue_body(
                        data["number"],
                        data.get("title", "N/A") + cat_str,
                        "open",
                        data.get("createdAt", ""),
                        data.get("body", ""),
                    )
                )
                _render_comments(data.get("comments", []))
                return

            elif len(parts) >= 4 and parts[2] == "issues" and parts[3].isdigit():
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                number = int(parts[3])
                reroute_message(
                    url, f"scout issue {owner}/{repo_name} {number}", "github.com issue"
                )
                from research._ghapi import APIError, view_issue
                from research._render import format_issue_body
                from research.scout.issues import _render_comments

                try:
                    data = view_issue(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                click.echo(
                    format_issue_body(
                        data["number"],
                        data.get("title", "N/A"),
                        data.get("state", "unknown"),
                        data.get("createdAt", ""),
                        data.get("body", ""),
                    )
                )
                _render_comments(data.get("comments", []))
                return

            elif len(parts) >= 4 and parts[2] in ("pull", "pulls") and parts[3].isdigit():
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                number = int(parts[3])
                reroute_message(url, f"scout pr {owner}/{repo_name} {number}", "github.com PR")
                from research._ghapi import APIError, view_pr
                from research._render import format_issue_body
                from research.scout.issues import _render_comments

                try:
                    data = view_pr(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                merged_at = data.get("mergedAt")
                state_str = data.get("state", "unknown")
                if merged_at:
                    state_str += f" (merged {merged_at[:10]})"
                click.echo(
                    format_issue_body(
                        data["number"],
                        data.get("title", "N/A"),
                        state_str,
                        data.get("createdAt", ""),
                        data.get("body", ""),
                    )
                )
                _render_comments(data.get("comments", []))
                return

            elif len(parts) >= 4 and parts[2] == "blob":
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                ref = parts[3]
                file_path = "/".join(parts[4:])
                reroute_message(
                    url,
                    f"scout cat {owner}/{repo_name} {file_path} --ref {ref}",
                    "github.com blob",
                )
                from research.scout._clone import ensure_ref, ensure_repo

                repo_dir = ensure_repo(owner, repo_name)
                sha = ensure_ref(owner, repo_name, ref)
                result_proc = subprocess.run(
                    ["git", "show", f"{sha}:{file_path}"],
                    capture_output=True,
                    text=True,
                    cwd=repo_dir,
                )
                if result_proc.returncode != 0:
                    click.echo(f"error: file not found: {file_path} at ref {ref}", err=True)
                    sys.exit(1)
                content = result_proc.stdout
                if find:
                    from research._render import apply_find

                    output = apply_find(content, find, context)
                else:
                    output = content
                click.echo(truncate_output(output, max_chars))
                return

            elif len(parts) >= 4 and parts[2] == "commit":
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                sha = parts[3]
                reroute_message(url, f"scout commit {owner}/{repo_name} {sha}", "github.com commit")
                from research._ghapi import APIError, view_commit
                from research._render import fenced_code, kv_line, section_heading

                try:
                    data = view_commit(owner, repo_name, sha)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                commit_obj = data.get("commit", {})
                committer = commit_obj.get("committer", {})
                author = commit_obj.get("author", {})
                click.echo(f"## Commit {sha[:8]}\n")
                click.echo(kv_line("Date", committer.get("date", "N/A")[:10]))
                click.echo(kv_line("Author", author.get("name", "N/A")))
                click.echo("")
                if commit_obj.get("message"):
                    click.echo(commit_obj["message"])
                stats = data.get("stats", {})
                if stats:
                    click.echo(
                        f"\n**Changes:** +{stats.get('additions', 0)} -{stats.get('deletions', 0)}"
                    )
                files = data.get("files", [])
                if files:
                    click.echo(section_heading("Files changed"))
                    for f in files:
                        click.echo(
                            f"\n**{f.get('filename', '?')}** ({f.get('status', 'modified')})"
                        )
                        if f.get("patch"):
                            click.echo(fenced_code(f["patch"], "diff"))
                return

            elif len(parts) >= 3 and parts[2] == "wiki":
                pass  # fall through to web fetch; wiki pages are HTML

            else:
                # Default: scout orient for bare owner/repo URLs
                cache = get_cache()
                budget_reserve(cache, url.split("?")[0].split("#")[0])
                reroute_message(url, f"scout orient {owner}/{repo_name}", "github.com pages")
                from research.scout.explore import _render_orient

                _render_orient(owner, repo_name, ref=None, brief=False)
                return

    if is_pdf_url(url):
        reroute_message(url, f"pdf {url}", "URL points to a PDF")
        from research.pdf import _do_pdf

        _do_pdf(url, find, context, max_chars)
        return

    base_url = url.split("?")[0]
    cache = get_cache()

    cached = read_cached_content(base_url)
    if cached is not None:
        markdown = cached
    else:
        budget_reserve(cache, base_url)
        try:
            markdown = fetch_markdown(url)
        except FetchError as e:
            msg = str(e)
            if "file, not an HTML page" in msg:
                reroute_message(url, f"pdf {url}", "response is a file, not HTML")
                from research.pdf import _do_pdf

                _do_pdf(url, find, context, max_chars)
                return
            budget_refund(cache, base_url)
            click.echo(f"error: fetch failed: {msg}", err=True)
            sys.exit(1)
        write_cached_content(base_url, markdown)

    if find:
        output = apply_find(markdown, find, context)
    else:
        output = markdown
    click.echo(truncate_output(output, max_chars))
