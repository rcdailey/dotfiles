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
    DEFAULT_SCOUT_MAX_CHARS,
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
@click.option("--max-results", type=click.IntRange(min=1, max=10), default=DEFAULT_MAX_RESULTS)
@click.option("--results", is_flag=True, help="return search results instead of a sourced answer")
@click.option("--critical", is_flag=True, help="use a reserved post-warning call")
def search_cmd(query: str, max_results: int, results: bool, critical: bool) -> None:
    """Search the web via Linkup."""
    sourced_answer = not results
    cache_key = f"{sourced_answer}:{max_results}:{query}"
    cached = read_cached_search(cache_key)
    if cached is not None:
        click.echo(cached)
        return

    cache = get_cache()
    budget_reserve(cache, None, critical=critical)

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
@click.option("--critical", is_flag=True, help="use a reserved post-warning call")
def fetch_cmd(
    url: str,
    find: str | None,
    context: int,
    max_chars: int,
    offset: int,
    critical: bool,
) -> None:
    """Fetch a URL as clean markdown."""
    # Check for reroutes before burning budget
    if is_github_url(url):
        path = strip_github_host(url)
        parts = path.split("/")

        # Skip non-repo paths; let them fall through to normal web fetch
        if len(parts) >= 2 and parts[0] not in ("orgs", "topics", "settings", "features"):
            owner, repo_name = parts[0], parts[1]

            if len(parts) >= 4 and parts[2] == "discussions" and parts[3].isdigit():
                number = int(parts[3])
                reroute_message(
                    url,
                    f"scout discussion {owner}/{repo_name} {number}",
                    "github.com discussion",
                )
                from research._ghapi import APIError, view_discussion
                from research._render import format_issue_body
                from research.scout.issues import _format_comments

                try:
                    data = view_discussion(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                category = data.get("category", {}).get("name", "")
                cat_str = f" [{category}]" if category else ""
                output = format_issue_body(
                    data["number"],
                    data.get("title", "N/A") + cat_str,
                    "open",
                    data.get("createdAt", ""),
                    data.get("body", ""),
                    url,
                )
                output += _format_comments(data.get("comments", []))
                click.echo(
                    truncate_output(
                        output,
                        DEFAULT_SCOUT_MAX_CHARS,
                        "use scout discussion for narrower follow-up",
                    )
                )
                return

            elif len(parts) >= 4 and parts[2] == "issues" and parts[3].isdigit():
                number = int(parts[3])
                reroute_message(
                    url, f"scout issue {owner}/{repo_name} {number}", "github.com issue"
                )
                from research._ghapi import APIError, view_issue
                from research._render import format_issue_body

                try:
                    data = view_issue(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                output = format_issue_body(
                    data["number"],
                    data.get("title", "N/A"),
                    data.get("state", "unknown"),
                    data.get("createdAt", ""),
                    data.get("body", ""),
                    url,
                )
                click.echo(
                    truncate_output(
                        output,
                        DEFAULT_SCOUT_MAX_CHARS,
                        "use scout issue for narrower follow-up",
                    )
                )
                return

            elif len(parts) >= 4 and parts[2] in ("pull", "pulls") and parts[3].isdigit():
                number = int(parts[3])
                reroute_message(url, f"scout pr {owner}/{repo_name} {number}", "github.com PR")
                from research._ghapi import APIError, view_pr
                from research._render import format_issue_body

                try:
                    data = view_pr(owner, repo_name, number)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                merged_at = data.get("mergedAt")
                state_str = data.get("state", "unknown")
                if merged_at:
                    state_str += f" (merged {merged_at[:10]})"
                output = format_issue_body(
                    data["number"],
                    data.get("title", "N/A"),
                    state_str,
                    data.get("createdAt", ""),
                    data.get("body", ""),
                    url,
                )
                click.echo(
                    truncate_output(
                        output,
                        DEFAULT_SCOUT_MAX_CHARS,
                        "use scout pr for narrower follow-up",
                    )
                )
                return

            elif len(parts) >= 5 and parts[2:4] == ["releases", "tag"]:
                tag = "/".join(parts[4:])
                reroute_message(url, f"scout release {owner}/{repo_name} {tag}", "GitHub release")
                from research._ghapi import APIError, view_release

                try:
                    data = view_release(owner, repo_name, tag)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                lines = [
                    f"## Release: {data.get('tagName', tag)}",
                    f"Source: {data.get('url') or url}",
                ]
                if data.get("publishedAt"):
                    lines.append(f"Published: {data['publishedAt'][:10]}")
                if data.get("body"):
                    lines.extend(["", data["body"]])
                click.echo(
                    truncate_output(
                        "\n".join(lines),
                        DEFAULT_SCOUT_MAX_CHARS,
                        "use linked PRs or commits for narrower evidence",
                    )
                )
                return

            elif len(parts) == 3 and parts[2] == "releases":
                reroute_message(url, f"scout release {owner}/{repo_name}", "GitHub releases")
                from research._ghapi import APIError, list_releases

                try:
                    releases = list_releases(owner, repo_name, 31)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                for release in releases[:30]:
                    tag = release.get("tagName", "N/A")
                    published = (release.get("publishedAt") or "")[:10] or "N/A"
                    source = release.get("url")
                    if not source:
                        source = f"https://github.com/{owner}/{repo_name}/releases/tag/{tag}"
                    click.echo(f"- {tag} ({published})\n  Source: {source}")
                if len(releases) > 30:
                    click.echo("... more results available; use scout release --limit 31")
                return

            elif len(parts) >= 4 and parts[2] == "blob":
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
                output = f"Source: {url}\n\n{output}"
                github_max = min(max_chars, DEFAULT_SCOUT_MAX_CHARS)
                if github_max <= 0:
                    github_max = DEFAULT_SCOUT_MAX_CHARS
                click.echo(truncate_output(output, github_max))
                return

            elif len(parts) >= 4 and parts[2] == "commit":
                sha = parts[3]
                reroute_message(url, f"scout commit {owner}/{repo_name} {sha}", "github.com commit")
                from research._ghapi import APIError, view_commit
                from research._render import kv_line, section_heading

                try:
                    data = view_commit(owner, repo_name, sha)
                except APIError as e:
                    click.echo(f"error: {e}", err=True)
                    sys.exit(1)
                commit_obj = data.get("commit", {})
                committer = commit_obj.get("committer", {})
                author = commit_obj.get("author", {})
                lines = [
                    f"## Commit {sha[:8]}\n",
                    kv_line("Date", committer.get("date", "N/A")[:10]),
                    kv_line("Author", author.get("name", "N/A")),
                    kv_line("Source", url),
                    "",
                ]
                if commit_obj.get("message"):
                    lines.append(commit_obj["message"])
                stats = data.get("stats", {})
                if stats:
                    lines.append(
                        f"\n**Changes:** +{stats.get('additions', 0)} -{stats.get('deletions', 0)}"
                    )
                files = data.get("files", [])
                if files:
                    lines.append(section_heading("Files changed"))
                    for f in files:
                        additions = f.get("additions", 0)
                        deletions = f.get("deletions", 0)
                        lines.append(
                            f"\n**{f.get('filename', '?')}** "
                            f"({f.get('status', 'modified')}, +{additions} -{deletions})"
                        )
                    lines.append("\nPatches omitted; use scout commit --patch for bounded diffs.")
                click.echo(
                    truncate_output(
                        "\n".join(lines),
                        DEFAULT_SCOUT_MAX_CHARS,
                        "use scout commit --path PATH for narrower evidence",
                    )
                )
                return

            elif len(parts) >= 3 and parts[2] == "wiki":
                pass  # fall through to web fetch; wiki pages are HTML

            elif len(parts) == 2:
                reroute_message(url, f"scout orient {owner}/{repo_name}", "github.com pages")
                from research.scout.explore import _render_orient

                _render_orient(owner, repo_name, ref=None, brief=True)
                return

    if is_pdf_url(url):
        reroute_message(url, f"pdf {url}", "URL points to a PDF")
        from research.pdf import _do_pdf

        _do_pdf(url, find, context, max_chars, offset, critical)
        return

    base_url = cache_url(url)
    cache = get_cache()

    cached = read_cached_content(base_url)
    if cached is not None:
        markdown = cached
    else:
        budget_reserve(cache, base_url, critical=critical)
        try:
            markdown = fetch_markdown(url)
        except FetchError as e:
            msg = str(e)
            if "file, not an HTML page" in msg:
                reroute_message(url, f"pdf {url}", "response is a file, not HTML")
                from research.pdf import _do_pdf

                _do_pdf(url, find, context, max_chars, offset, critical)
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

    click.echo(truncate_output(output, max_chars), nl=False)
