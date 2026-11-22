"""Closing command: checks the goal report, then lists citable sources and failures."""

from __future__ import annotations

import json
import sys

import click

from research import errors, sources
from research._cache import get_session_id
from research._error_ledger import record_error
from research._goals import (
    MAX_REJECTIONS,
    check_report,
    get_goals,
    goals_required,
    record_rejection,
    rejections,
    unread_summary,
)


def _goal_table(goals: list[str], report: list[dict]) -> str:
    by_number = {e.get("goal"): e for e in report if isinstance(e, dict)}
    lines = []
    for number, goal in enumerate(goals, 1):
        entry = by_number.get(number, {})
        if entry.get("status") == "supported":
            outcome = "supported: " + ", ".join(entry.get("sources") or [])
        elif entry.get("status") == "gap":
            outcome = f"gap ({entry.get('kind')}): {entry.get('reason')}"
        else:
            outcome = "not reported"
        lines.append(f"{number}. {goal}\n   {outcome}")
    return "\n".join(lines)


@click.command()
@click.option(
    "--report",
    help='JSON list: {"goal": N, "status": "supported", "sources": [url]} or '
    '{"goal": N, "status": "gap", "kind": "not_found|out_of_budget", "reason": "..."}; '
    "required once goals are recorded or required",
)
@click.pass_context
def cli(ctx: click.Context, report: str | None) -> None:
    """List citable sources and failures; with goals, first check each goal's reported outcome."""
    if report is None:
        if goals_required() or get_goals():
            raise click.UsageError("--report is required: report every recorded goal")
        _print_sources_and_errors(ctx)
        return
    if get_session_id() is None:
        click.echo("error: the closing report needs a research session", err=True)
        sys.exit(2)
    try:
        entries = json.loads(report)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"--report is not valid JSON: {e}") from None
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise click.UsageError("--report must be a JSON list of objects")

    goals = get_goals()
    if not goals:
        click.echo("error: no goals recorded; record them with research_plan first", err=True)
        sys.exit(2)
    problems = check_report(entries)
    if problems and rejections() < MAX_REJECTIONS:
        attempt = record_rejection()
        click.echo(f"Report rejected ({attempt} of {MAX_REJECTIONS}); fix these and call again:")
        click.echo("\n".join(f"- {p}" for p in problems))
        if unread := unread_summary():
            click.echo(f"\n{unread}")
        return
    for problem in problems:
        record_error(
            ["ledger"], f"unresolved after {MAX_REJECTIONS} rejections: {problem}", "coverage"
        )

    click.echo(f"## Goals\n\n{_goal_table(goals, entries)}\n")
    _print_sources_and_errors(ctx)


def _print_sources_and_errors(ctx: click.Context) -> None:
    click.echo("## Sources\n")
    ctx.invoke(sources.cli)
    click.echo("\n## Errors\n")
    ctx.invoke(errors.cli)
