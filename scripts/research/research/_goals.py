"""Per-session research goals, seen search results, and the checks on the closing report.

A researcher records its goals before retrieving anything and closes by reporting each goal as
supported (with URLs it read) or as a gap. Checks use only what the tools recorded, never the
agent's own account, because agents overclaim completion. They cannot judge whether a cited page
really supports a goal or whether a "not found" gap is honest; that ceiling is deliberate, since
stricter required fields push models to invent answers.
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterable

import click

from research._budget import WARNING_AT, get_count
from research._cache import get_cache, get_session_id
from research._search_results import url_key
from research._source_ledger import get_sources

_EXPIRY_SECONDS = 24 * 3600
# Rejected closing reports before the next one is accepted with its problems recorded, so a
# researcher that cannot satisfy the checks still returns its evidence instead of looping.
MAX_REJECTIONS = 2
_DISCOVERED = re.compile(r"^\s*Discovered: (\S+)", re.MULTILINE)
_UNREAD_LISTED = 10


def _key(name: str) -> str | None:
    session_id = get_session_id()
    return f"research:{session_id}:{name}" if session_id else None


def get_goals() -> list[str]:
    key = _key("goals")
    return list(get_cache().get(key, [])) if key else []


def add_goals(goals: Iterable[str]) -> list[str]:
    """Append new goals; goals cannot be removed, so the task cannot shrink to fit the findings."""
    key = _key("goals")
    if key is None:
        return []
    cache = get_cache()
    with cache.transact():
        current = list(cache.get(key, []))
        for goal in (g.strip() for g in goals):
            if goal and goal not in current:
                current.append(goal)
        cache.set(key, current, expire=_EXPIRY_SECONDS)
    return current


def goals_required() -> bool:
    """Whether the calling agent follows the goal protocol; the OpenCode plugin decides per agent,
    so other agents and manual CLI use keep working without goals."""
    return get_session_id() is not None and os.environ.get("RESEARCH_REQUIRE_GOALS") == "1"


def require_goals() -> None:
    """Refuse retrieval until goals are recorded, for agents that follow the goal protocol."""
    if not goals_required() or get_goals():
        return
    click.echo(
        "error: record your goals with research_plan before searching or reading: one goal per "
        "fact or track the caller asked for",
        err=True,
    )
    sys.exit(2)


def record_seen(rendered_search: str) -> None:
    """Remember result URLs shown by a search, so a closing report can list unread ones."""
    key = _key("seen")
    urls = _DISCOVERED.findall(rendered_search)
    if key is None or not urls:
        return
    cache = get_cache()
    with cache.transact():
        seen = list(cache.get(key, []))
        seen.extend(u for u in urls if u not in seen)
        cache.set(key, seen, expire=_EXPIRY_SECONDS)


def unread_results() -> list[str]:
    """Search-result URLs shown this session that no tool has read."""
    key = _key("seen")
    seen = list(get_cache().get(key, [])) if key else []
    read = {url_key(u) for u in get_sources()}
    return [u for u in seen if url_key(u) not in read]


def check_report(report: list[dict]) -> list[str]:
    """Return one problem per goal that the recorded session facts contradict."""
    goals = get_goals()
    read = {url_key(u) for u in get_sources()}
    ordinary_left = max(WARNING_AT - get_count(get_cache()), 0)
    problems: list[str] = []
    reported: set[int] = set()
    for entry in report:
        number = entry.get("goal")
        if not isinstance(number, int) or not 1 <= number <= len(goals):
            problems.append(f"goal {number!r}: no such goal; goals are numbered 1-{len(goals)}")
            continue
        reported.add(number)
        status = entry.get("status")
        if status == "supported":
            urls = [u for u in entry.get("sources") or [] if isinstance(u, str)]
            if not any(url_key(u) in read for u in urls):
                cited = ", ".join(urls) or "none"
                problems.append(
                    f"goal {number}: cites no URL read in this session (cited: {cited}); search "
                    "results are not evidence; read a page first or report a gap"
                )
        elif status == "gap":
            kind = entry.get("kind")
            if not str(entry.get("reason") or "").strip():
                problems.append(f"goal {number}: gap needs a reason")
            if kind == "out_of_budget" and ordinary_left:
                problems.append(
                    f"goal {number}: reported out of budget, but {ordinary_left} ordinary budget "
                    "calls remain; spend them on this goal or report what was searched as "
                    "not_found"
                )
            elif kind not in ("not_found", "out_of_budget"):
                problems.append(f"goal {number}: gap kind must be not_found or out_of_budget")
        else:
            problems.append(f"goal {number}: status must be supported or gap")
    problems.extend(
        f"goal {n}: missing from the report" for n in range(1, len(goals) + 1) if n not in reported
    )
    return problems


def record_rejection() -> int:
    """Count one rejected closing report and return the total so far."""
    key = _key("close_rejections")
    if key is None:
        return 0
    cache = get_cache()
    with cache.transact():
        count = cache.get(key, 0) + 1
        cache.set(key, count, expire=_EXPIRY_SECONDS)
    return count


def rejections() -> int:
    key = _key("close_rejections")
    return get_cache().get(key, 0) if key else 0


def unread_summary() -> str:
    unread = unread_results()
    if not unread:
        return ""
    listed = "\n".join(f"- {u}" for u in unread[:_UNREAD_LISTED])
    more = f"\n- ... {len(unread) - _UNREAD_LISTED} more" if len(unread) > _UNREAD_LISTED else ""
    return f"{len(unread)} search results seen but never read:\n{listed}{more}"
