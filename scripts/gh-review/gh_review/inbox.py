"""List PRs awaiting your review, with the deltas since your last pass."""

from __future__ import annotations

import re
import textwrap
from datetime import datetime

import click

from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql, split_repo
from gh_review._sanitize import is_bot, truncate_body

COMMENT_PREVIEW = 200

_TICKET_RE = re.compile(r"[A-Z]{2,}-\d+")

_INBOX_QUERY = textwrap.dedent("""\
    query($owner:String!, $repo:String!) {
      viewer { login }
      repository(owner:$owner, name:$repo) {
        pullRequests(states:OPEN, first:50,
                     orderBy:{field:UPDATED_AT, direction:DESC}) {
          nodes {
            number title isDraft updatedAt
            author { login }
            commits(last:30) {
              nodes { commit { abbreviatedOid committedDate messageHeadline } }
            }
            reviews(first:50) {
              nodes { author { login __typename } submittedAt }
            }
            reviewThreads(first:100) {
              nodes {
                comments(first:50) {
                  nodes { author { login __typename } createdAt body path }
                }
              }
            }
            comments(first:100) {
              nodes { author { login __typename } createdAt body }
            }
          }
        }
      }
    }""")


def _parse(ts: str) -> datetime:
    """Parse a GitHub ISO-8601 timestamp into an aware datetime."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _ticket(title: str) -> str:
    """Extract a Linear/GitHub ticket key from a PR title, or '-'."""
    m = _TICKET_RE.search(title)
    return m.group(0) if m else "-"


def _my_last_review(reviews: list[dict], me: str) -> datetime | None:
    """Latest submission time of the viewer's own reviews, or None."""
    mine = [
        _parse(r["submittedAt"])
        for r in reviews
        if r["submittedAt"] and r["author"] and r["author"]["login"] == me
    ]
    return max(mine) if mine else None


def _new_commits(commits: list[dict], since: datetime) -> list[dict]:
    """Commits landed after the given time, oldest first."""
    out = [c["commit"] for c in commits if _parse(c["commit"]["committedDate"]) > since]
    out.sort(key=lambda c: c["committedDate"])
    return out


def _new_comments(pr: dict, me: str, since: datetime) -> list[dict]:
    """Human replies in the viewer's threads and PR-level comments since `since`.

    A thread counts only when the viewer commented in it; a later comment from
    anyone else in that thread is a follow-up. PR-level comments from others
    always count. Bots and the viewer are excluded as authors.
    """
    out: list[dict] = []
    for thread in pr["reviewThreads"]["nodes"]:
        nodes = thread["comments"]["nodes"]
        if not any(c["author"] and c["author"]["login"] == me for c in nodes):
            continue
        path = next((c.get("path") for c in nodes if c.get("path")), None)
        for c in nodes:
            out.append({**c, "where": f"thread {path}" if path else "thread"})
    for c in pr["comments"]["nodes"]:
        out.append({**c, "where": "pr comment"})

    seen = []
    for c in out:
        author = c["author"]
        if (
            not author
            or author["login"] == me
            or is_bot(author["login"], author.get("__typename", ""))
        ):
            continue
        if _parse(c["createdAt"]) <= since:
            continue
        seen.append(c)
    seen.sort(key=lambda c: c["createdAt"])
    return seen


def _render(pr: dict, me: str) -> str | None:
    """Render one PR block, or None if it should not appear in the inbox."""
    if pr["isDraft"]:
        return None
    author = pr["author"]["login"] if pr["author"] else "unknown"
    if author == me:
        return None

    num = pr["number"]
    ticket = _ticket(pr["title"])
    header = f"#{num}  {{label}}  {author}  {ticket}  {pr['title'].strip()}"

    last = _my_last_review(pr["reviews"]["nodes"], me)
    if last is None:
        head = pr["commits"]["nodes"][-1]["commit"] if pr["commits"]["nodes"] else None
        head_date = head["committedDate"] if head else pr["updatedAt"]
        return header.format(label="NEW") + f"\n  never reviewed; head {head_date}"

    commits = _new_commits(pr["commits"]["nodes"], last)
    comments = _new_comments(pr, me, last)
    since = last.isoformat().replace("+00:00", "Z")

    if not commits and not comments:
        return (
            header.format(label="SKIP")
            + f"\n  no new commits or comments since your review ({since})"
        )

    label = "RE-REVIEW" if commits else "REPLY"
    lines = [header.format(label=label)]
    if commits:
        lines.append(f"  {len(commits)} commit(s) since your review ({since}):")
        lines += [f"    - {c['abbreviatedOid']} {c['messageHeadline']}" for c in commits]
    if comments:
        lines.append(f"  {len(comments)} new comment(s):")
        for c in comments:
            body = truncate_body(" ".join(c["body"].split()), COMMENT_PREVIEW)
            lines.append(f"    - {c['author']['login']} ({c['where']}): {body}")
    return "\n".join(lines)


@click.command()
@click.argument("repo")
def cli(repo: str) -> None:
    """List open PRs awaiting your review and what changed since your last pass."""
    owner, name = split_repo(repo)
    try:
        data = gh_graphql(_INBOX_QUERY, owner=owner, repo=name)
    except GhError as exc:
        die(str(exc))

    me = data["data"]["viewer"]["login"]
    prs = data["data"]["repository"]["pullRequests"]["nodes"]
    blocks = [b for b in (_render(pr, me) for pr in prs) if b]

    if not blocks:
        click.echo(f"no open PRs awaiting your review in {repo}")
        return
    click.echo("\n\n".join(blocks))
