"""Shared concise renderers for Linear models."""

from __future__ import annotations

import click

from linear_cli._models import Comment, Issue, ProjectUpdate, priority_label

_UPDATE_PREVIEW_LEN = 200
CLOSED_STATE_TYPES = frozenset({"completed", "canceled", "duplicate"})
# Active work first; priority is deliberately ignored because many teams leave it unset.
_STATE_ORDER = {"started": 0, "unstarted": 1, "backlog": 2, "triage": 3}
_OTHER_OPEN_RANK = len(_STATE_ORDER)
_CLOSED_RANK = _OTHER_OPEN_RANK + 1


def is_open(issue: Issue) -> bool:
    """Return whether an issue still needs work (not completed, canceled, or duplicate)."""
    return issue.state_type not in CLOSED_STATE_TYPES


def sort_issues(issues: list[Issue]) -> list[Issue]:
    """Order issues by state (started, unstarted, backlog, triage, closed), newest update first."""

    def rank(issue: Issue) -> int:
        if not is_open(issue):
            return _CLOSED_RANK
        return _STATE_ORDER.get(issue.state_type or "", _OTHER_OPEN_RANK)

    by_updated = sorted(issues, key=lambda issue: issue.updated_at or "", reverse=True)
    return sorted(by_updated, key=rank)


def estimate_text(estimate: float | None) -> str:
    """Format an issue estimate."""
    if estimate is None:
        return "-"
    return str(int(estimate)) if estimate == int(estimate) else str(estimate)


def percentage_text(value: float | None) -> str:
    """Format an API percentage value."""
    return f"{value:.0f}%" if value is not None else "0%"


def echo_issue_summary(issue: Issue, *, indent: str = "") -> None:
    """Print one issue summary line."""
    parts = [
        (
            f"{indent}{issue.identifier}  {issue.state_name}  "
            f"[{priority_label(issue.priority)}]  {issue.title}"
        )
    ]
    if issue.assignee_name:
        parts.append(f"assignee: {issue.assignee_name}")
    if issue.labels:
        parts.append(f"labels: {', '.join(issue.labels)}")
    parts.append(f"estimate: {estimate_text(issue.estimate)}")
    parts.append(issue_times_text(issue))
    click.echo("  ".join(parts))


def issue_times_text(issue: Issue) -> str:
    """Format issue lifecycle timestamps, omitting stages the issue has not reached."""
    times = [
        ("created", issue.created_at),
        ("started", issue.started_at),
        ("completed", issue.completed_at),
        ("updated", issue.updated_at),
    ]
    return "  ".join(f"{label}: {value}" for label, value in times if value)


def echo_project_update(update: ProjectUpdate, *, full: bool, indent: str = "") -> None:
    """Print one project update header and its body, previewed unless ``full``."""
    suffix = f" ({update.project_name})" if update.project_name else ""
    click.echo(f"{indent}[{update.health}] {update.created_at} by {update.user_name}{suffix}")
    body = update.body or ""
    if not full and len(body) > _UPDATE_PREVIEW_LEN:
        body = body[:_UPDATE_PREVIEW_LEN] + "... [truncated; pass --full]"
    for line in body.splitlines():
        click.echo(f"{indent}  {line}" if line else "")


def _echo_comment(comment: Comment, indent: str) -> None:
    header = f"{indent}{comment.id}  {comment.created_at}  {comment.author}"
    if comment.synced_services:
        header += f"  synced: {', '.join(comment.synced_services)}"
    click.echo(header)
    for line in (comment.body or "").splitlines():
        click.echo(f"{indent}  {line}" if line else "")


def echo_comments(comments: list[Comment]) -> None:
    """Print comments as threads: each root followed by its indented replies, oldest first.

    A reply whose root is outside ``comments`` prints as a root so no comment is dropped.
    """
    ordered = sorted(comments, key=lambda c: c.created_at or "")
    ids = {c.id for c in ordered}
    replies: dict[str, list[Comment]] = {}
    for comment in ordered:
        if comment.parent_id in ids:
            replies.setdefault(comment.parent_id, []).append(comment)
    for comment in ordered:
        if comment.parent_id in ids:
            continue
        _echo_comment(comment, "")
        for reply in replies.get(comment.id, []):
            _echo_comment(reply, "  ")
