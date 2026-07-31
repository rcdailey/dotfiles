"""Web search and fetch subcommand."""

from __future__ import annotations

import subprocess
import sys

import click

from research._budget import budget_refund, budget_reserve
from research._cache import (
    cache_url,
    get_cache,
    read_cached_content,
    read_cached_search,
    write_cached_content,
    write_cached_search,
)
from research._fetch import FetchError, fetch_markdown
from research._linkup import SearchError, format_search_results, format_sourced_answer
from research._render import (
    DEFAULT_MAX_CHARS,
    apply_find,
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
@click.option("--results", is_flag=True, help="return search results instead of a sourced answer")
def search_cmd(query: str, max_results: int, results: bool) -> None:
    """Search the web via Linkup."""
    sourced_answer = not results
    cache_key = f"{sourced_answer}:{max_results}:{query}"
    cached = read_cached_search(cache_key)
    if cached is not None:
        click.echo(cached)
        return

    cache = get_cache()
    budget_reserve(cache, None)

    try:
        from research._linkup import search

        response = search(query, max_results, sourced_answer)
        rendered = (
            format_sourced_answer(response)
            if sourced_answer
            else format_search_results(response.results)
        )
        write_cached_search(cache_key, rendered)
        click.echo(rendered)
    except SearchError as e:
        budget_refund(cache)
        click.echo(f"error: {e}", err=True)
        sys.exit(1)


@cli.command(name="fetch")
@click.argument("url")
@click.option("--find", help="show only paragraphs matching this pattern")
@click.option("-C", "--context", type=int, default=0, help="paragraphs of context around matches")
@click.option("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
@click.option("--offset", type=int, default=0, help="char offset into content for pagination")
def fetch_cmd(url: str, find: str | None, context: int, max_chars: int, offset: int) -> None:
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
                budget_reserve(cache, cache_url(url))
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
                budget_reserve(cache, cache_url(url))
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
                budget_reserve(cache, cache_url(url))
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
                budget_reserve(cache, cache_url(url))
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
                    check=False,
                )
                if result_proc.returncode != 0:
                    click.echo(f"error: file not found: {file_path} at ref {ref}", err=True)
                    sys.exit(1)
                content = result_proc.stdout
                if find:
                    output = apply_find(content, find, context)
                else:
                    output = content
                click.echo(truncate_output(output, max_chars))
                return

            elif len(parts) >= 4 and parts[2] == "commit":
                cache = get_cache()
                budget_reserve(cache, cache_url(url))
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
                budget_reserve(cache, cache_url(url))
                reroute_message(url, f"scout orient {owner}/{repo_name}", "github.com pages")
                from research.scout.explore import _render_orient

                _render_orient(owner, repo_name, ref=None, brief=False)
                return

    if is_pdf_url(url):
        reroute_message(url, f"pdf {url}", "URL points to a PDF")
        from research.pdf import _do_pdf

        _do_pdf(url, find, context, max_chars, offset)
        return

    base_url = cache_url(url)
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

                _do_pdf(url, find, context, max_chars, offset)
                return
            budget_refund(cache, base_url)
            click.echo(f"error: fetch failed: {msg}", err=True)
            sys.exit(1)
        write_cached_content(base_url, markdown)

    total_len = len(markdown)
    if offset > 0:
        markdown = markdown[offset:]

    if find:
        output = apply_find(markdown, find, context)
    else:
        output = markdown

    if offset > 0:
        output = f"[starting at char offset {offset}; total length {total_len}]\n\n" + output

    click.echo(truncate_output(output, max_chars))
