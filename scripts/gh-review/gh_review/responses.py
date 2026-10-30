"""Report replies and reactions to your PR comments since the last acknowledged check."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

import click

from gh_review._click import HelpfulGroup
from gh_review._errors import GhError, die
from gh_review._gh import gh_graphql_mutation, gh_rest_json, gh_rest_pages
from gh_review._responses_state import load_checked, save_checked, scope_key
from gh_review._sanitize import is_bot, sanitize_bot_body, truncate_body

FIRST_RUN_LOOKBACK = timedelta(days=1)
# Reactions do not bump a PR's updatedAt, so candidate PRs come from a window reaching back
# before the last check. A reaction on a PR untouched for longer than this goes unreported;
# widen the window if that becomes a real miss.
CANDIDATE_WINDOW = timedelta(days=7)
BATCH = 10
ABOUT_CHARS = 300
MINE_CHARS = 600
REPLY_CHARS = 1500

EMOJI = {
    "THUMBS_UP": "\U0001f44d",
    "THUMBS_DOWN": "\U0001f44e",
    "LAUGH": "\U0001f604",
    "HOORAY": "\U0001f389",
    "CONFUSED": "\U0001f615",
    "HEART": "\u2764\ufe0f",
    "ROCKET": "\U0001f680",
    "EYES": "\U0001f440",
}

# Timeline items that never raise a notification worth reading on their own.
_QUIET_EVENTS = frozenset(
    {
        "LabeledEvent",
        "UnlabeledEvent",
        "SubscribedEvent",
        "UnsubscribedEvent",
        "CrossReferencedEvent",
        "ReferencedEvent",
        "MilestonedEvent",
        "DemilestonedEvent",
        "ConnectedEvent",
        "DisconnectedEvent",
        "CommentDeletedEvent",
        "HeadRefDeletedEvent",
        "AddedToProjectV2Event",
        "ProjectV2ItemStatusChangedEvent",
    }
)

_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_SEARCH = """
query($q:String!, $after:String) {
  search(query:$q, type:ISSUE, first:100, after:$after) {
    pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest { id } }
  }
}"""

_REACTIONS = "reactions(last:10) { nodes { content createdAt user { login } } }"

_DETAILS = f"""
query($ids:[ID!]!, $me:String!) {{
  nodes(ids:$ids) {{
    ... on PullRequest {{
      id number title body repository {{ nameWithOwner }} author {{ login }}
      reviewThreads(first:60) {{ nodes {{ path comments(first:30) {{ nodes {{
        id body createdAt author {{ login __typename }} {_REACTIONS}
      }} }} }} }}
      comments(last:50) {{ nodes {{ id body createdAt author {{ login }} {_REACTIONS} }} }}
      reviews(author:$me, last:30) {{ nodes {{ id body createdAt {_REACTIONS} }} }}
    }}
  }}
}}"""

_TIMELINE_FIELDS = """
__typename
... on PullRequestReview {
  author { login } state body comments(first:50) { nodes { replyTo { id } } }
}
... on IssueComment { author { login } }
... on PullRequestCommit { commit { author { user { login } } } }
... on ReviewRequestedEvent { actor { login } }
... on HeadRefForcePushedEvent { actor { login } }
... on MergedEvent { actor { login } }
... on ClosedEvent { actor { login } }
... on ReopenedEvent { actor { login } }
... on ReadyForReviewEvent { actor { login } }
... on ConvertToDraftEvent { actor { login } }
... on AssignedEvent { actor { login } }
"""


@dataclass
class _Mine:
    """One of your comments and the responses to it that arrived since the last check."""

    where: str
    body: str
    # (createdAt, rendered response) for each reply or reaction.
    events: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class _Pr:
    node_id: str
    repo: str
    number: int
    title: str
    author: str
    about: str
    mine: list[_Mine]
    # First comment ID of each review thread you commented in; replies there are expected.
    thread_roots: set[str]

    @property
    def ref(self) -> str:
        return f"{self.repo}#{self.number}"


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _login(node: dict) -> str:
    return (node.get("author") or {}).get("login", "")


def _query(query: str, variables: dict) -> dict:
    try:
        return gh_graphql_mutation(query, variables)["data"]
    except GhError as exc:
        die(str(exc))


def _search_ids(query: str) -> list[str]:
    ids: list[str] = []
    after = None
    while True:
        page = _query(_SEARCH, {"q": query, "after": after})["search"]
        ids += [n["id"] for n in page["nodes"] if n]
        if not page["pageInfo"]["hasNextPage"]:
            return ids
        after = page["pageInfo"]["endCursor"]


def _new_reactions(node: dict, me: str, since: str) -> list[tuple[str, str]]:
    return [
        (r["createdAt"], f"{EMOJI.get(r['content'], r['content'])} {r['user']['login']}")
        for r in node["reactions"]["nodes"]
        if r["user"]
        and r["user"]["login"] != me
        and not is_bot(r["user"]["login"])
        and r["createdAt"] > since
    ]


def _collect(pr: dict, me: str, since: str) -> _Pr:
    """Gather your comments on one PR that got a reply or reaction after `since`.

    A thread reply belongs to your latest comment above it in that thread. Bots are ignored.
    Conversation comments and review summaries cannot be replied to, so only their reactions
    count.
    """
    entries: dict[str, _Mine] = {}
    roots: set[str] = set()

    def entry(comment: dict, where: str) -> _Mine:
        return entries.setdefault(comment["id"], _Mine(where, _flat(comment["body"])))

    for thread in pr["reviewThreads"]["nodes"]:
        comments = thread["comments"]["nodes"]
        if not any(_login(c) == me for c in comments):
            continue
        roots.add(comments[0]["id"])
        where = f"thread on {thread['path']}" if thread["path"] else "thread"
        last_mine = None
        for c in comments:
            login = _login(c)
            if login == me:
                last_mine = c
                if reactions := _new_reactions(c, me, since):
                    entry(c, where).events += reactions
            elif (
                last_mine
                and c["createdAt"] > since
                and not is_bot(login, (c.get("author") or {}).get("__typename", ""))
            ):
                body = truncate_body(_flat(c["body"]), REPLY_CHARS)
                entry(last_mine, where).events.append((c["createdAt"], f"{login} replied: {body}"))

    for c in pr["comments"]["nodes"]:
        if _login(c) == me and (reactions := _new_reactions(c, me, since)):
            entry(c, "conversation comment").events += reactions
    for r in pr["reviews"]["nodes"]:
        if r["body"].strip() and (reactions := _new_reactions(r, me, since)):
            entry(r, "review summary").events += reactions

    return _Pr(
        node_id=pr["id"],
        repo=pr["repository"]["nameWithOwner"],
        number=pr["number"],
        title=_flat(pr["title"]),
        author=_login(pr) or "unknown",
        about=truncate_body(_flat(sanitize_bot_body(pr["body"] or "")), ABOUT_CHARS),
        mine=[m for m in entries.values() if m.events],
        thread_roots=roots,
    )


def _actor(item: dict) -> str:
    if "commit" in item:
        return ((item["commit"].get("author") or {}).get("user") or {}).get("login", "")
    return (item.get("actor") or item.get("author") or {}).get("login", "")


def _is_quiet(item: dict, me: str, roots: set[str]) -> bool:
    """True when a timeline item is yours, inert, or a reply in one of your threads."""
    kind = item["__typename"]
    if kind in _QUIET_EVENTS or _actor(item) == me:
        return True
    if kind != "PullRequestReview" or item["state"] != "COMMENTED" or item["body"].strip():
        return False
    replies = item["comments"]["nodes"]
    return bool(replies) and all((c["replyTo"] or {}).get("id") in roots for c in replies)


def _other_activity(prs: list[_Pr], last_read: dict[str, str | None], me: str) -> dict[str, str]:
    """Map each PR node ID to a description of unread activity besides your responses.

    An empty description means the notification holds nothing but replies in your threads and
    inert events, so marking it read hides nothing.
    """
    out: dict[str, str] = {}
    for start in range(0, len(prs), BATCH):
        batch = prs[start : start + BATCH]
        aliases = []
        for i, pr in enumerate(batch):
            since = last_read[pr.node_id]
            since_arg = f"since:{json.dumps(since)}, " if since else ""
            aliases.append(
                f"p{i}: node(id:{json.dumps(pr.node_id)}) {{ ... on PullRequest {{ "
                f"timelineItems({since_arg}first:100) {{ pageInfo {{ hasNextPage }} "
                f"nodes {{ {_TIMELINE_FIELDS} }} }} }} }}"
            )
        data = _query("query {" + "\n".join(aliases) + "}", {})
        for i, pr in enumerate(batch):
            timeline = data[f"p{i}"]["timelineItems"]
            if timeline["pageInfo"]["hasNextPage"]:
                out[pr.node_id] = "over 100 timeline items"
                continue
            loud = Counter(
                n["__typename"] for n in timeline["nodes"] if not _is_quiet(n, me, pr.thread_roots)
            )
            out[pr.node_id] = ", ".join(f"{count} {kind}" for kind, count in loud.items())
    return out


def _unread_pr_notifications() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for n in gh_rest_pages("notifications"):
        if n["subject"]["type"] != "PullRequest" or not n["subject"].get("url"):
            continue
        number = int(n["subject"]["url"].rsplit("/", 1)[1])
        out[(n["repository"]["full_name"].lower(), number)] = n
    return out


def _render_pr(pr: _Pr) -> list[str]:
    lines = [f"{pr.ref} by {pr.author}: {pr.title}"]
    if pr.about:
        lines.append(f"About: {pr.about}")
    return lines


def _local(ts: str) -> datetime:
    """Convert a GitHub UTC timestamp to the machine's local timezone."""
    return datetime.fromisoformat(ts).astimezone()


def _day_heading(day: date, today: date) -> str:
    age = (today - day).days
    relative = "Today" if age == 0 else "Yesterday" if age == 1 else f"{age} days ago"
    return f"## {relative}, {day:%A %b} {day.day}"


def _render(prs: list[_Pr], today: date) -> list[str]:
    """Render responses grouped by local day (newest first), then PR, then your comment.

    A PR or comment with responses on several days appears under each of those days.
    """
    days: dict[date, dict[int, tuple[_Pr, dict[int, tuple[_Mine, list]]]]] = defaultdict(dict)
    for pr in prs:
        for m in pr.mine:
            for created, text in m.events:
                moment = _local(created)
                _, mines = days[moment.date()].setdefault(id(pr), (pr, {}))
                mines.setdefault(id(m), (m, []))[1].append((moment, text))

    lines: list[str] = []
    for day in sorted(days, reverse=True):
        lines += ["", _day_heading(day, today)]
        for pr, mines in days[day].values():
            lines += ["", *_render_pr(pr)]
            for m, events in mines.values():
                lines.append(f"- Your {m.where}: {truncate_body(m.body, MINE_CHARS)}")
                lines += [f"  {t:%-I:%M %p} {text}" for t, text in sorted(events)]
    return lines


def _scope_options(fn: Callable) -> Callable:
    fn = click.option(
        "--exclude-org", metavar="ORG", help="Skip PRs in this org (e.g. personal view)."
    )(fn)
    return click.option("--org", metavar="ORG", help="Only PRs in this org (e.g. work view).")(fn)


def _scope(org: str | None, exclude_org: str | None) -> tuple[str, str, list[str]]:
    """Return the state key, search qualifier, and matching CLI flags for an org filter."""
    if org and exclude_org:
        raise click.UsageError("--org and --exclude-org are mutually exclusive")
    key = scope_key(org, exclude_org)
    if org:
        return key, f"org:{org}", ["--org", org]
    if exclude_org:
        return key, f"-org:{exclude_org}", ["--exclude-org", exclude_org]
    return key, "", []


@click.group(cls=HelpfulGroup)
def cli() -> None:
    """Track replies and reactions to your PR comments across repos."""


@cli.command()
@_scope_options
def show(org: str | None, exclude_org: str | None) -> None:
    """Show replies and reactions since the last ack; changes nothing.

    The first run for a scope looks back one day. Ends with the exact `ack` command that
    records this check and marks notifications read when only your responses made them unread.
    """
    key, qualifier, flags = _scope(org, exclude_org)
    now = datetime.now(UTC)
    until = _stamp(now)
    try:
        since = load_checked(key) or _stamp(now - FIRST_RUN_LOOKBACK)
    except GhError as exc:
        die(f"cannot read state gist: {exc}")

    window = (datetime.fromisoformat(since) - CANDIDATE_WINDOW).date().isoformat()
    ids: list[str] = []
    for who in ("author", "reviewed-by", "commenter"):
        q = f"is:pr {who}:@me updated:>={window} {qualifier}".strip()
        ids += [i for i in _search_ids(q) if i not in ids]

    me = _query("query { viewer { login } }", {})["viewer"]["login"]
    prs: list[_Pr] = []
    for start in range(0, len(ids), BATCH):
        nodes = _query(_DETAILS, {"ids": ids[start : start + BATCH], "me": me})["nodes"]
        prs += [p for n in nodes if n and (p := _collect(n, me, since)).mine]

    local_now = now.astimezone()
    click.echo(
        f"Scope {key}; responses after {_local(since):%a %Y-%m-%d %-I:%M %p}; "
        f"times in {local_now:%Z}."
    )
    if not prs:
        click.echo("No new replies or reactions.")
    else:
        click.echo("\n".join(_render(prs, local_now.date())))

    try:
        notifications = _unread_pr_notifications()
    except GhError as exc:
        die(f"cannot list notifications: {exc}")
    unread = [pr for pr in prs if (pr.repo.lower(), pr.number) in notifications]
    thread = {pr.node_id: notifications[(pr.repo.lower(), pr.number)] for pr in unread}
    other = _other_activity(unread, {k: v["last_read_at"] for k, v in thread.items()}, me)
    to_read = [pr for pr in unread if not other[pr.node_id]]
    kept = [pr for pr in unread if other[pr.node_id]]

    click.echo("")
    if to_read:
        click.echo("Mark read: " + ", ".join(pr.ref for pr in to_read) + ".")
    for pr in kept:
        click.echo(f"Leave unread {pr.ref}: other activity ({other[pr.node_id]}).")
    ack = ["gh-review", "responses", "ack", *flags, "--until", until]
    if to_read:
        ack += ["--read", ",".join(thread[pr.node_id]["id"] for pr in to_read)]
    click.echo("After summarizing, run: " + " ".join(ack))


@cli.command()
@_scope_options
@click.option("--until", required=True, help="Time printed by `show`; the next run starts here.")
@click.option("--read", "read_ids", default="", help="Comma-separated notification thread IDs.")
def ack(org: str | None, exclude_org: str | None, until: str, read_ids: str) -> None:
    """Record a `show` run as seen and mark its notifications read."""
    key, _, _ = _scope(org, exclude_org)
    if not _TIMESTAMP.match(until):
        raise click.UsageError("--until must look like 2026-01-31T12:00:00Z")
    ids = [i for i in read_ids.split(",") if i]
    try:
        for thread_id in ids:
            gh_rest_json("PATCH", f"notifications/threads/{thread_id}")
        save_checked(key, until)
    except GhError as exc:
        die(str(exc))
    click.echo(f"Marked {len(ids)} notification(s) read; scope {key} checked through {until}.")
