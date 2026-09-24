"""Shared concise renderers for Linear models."""

from __future__ import annotations

import click

from linear_cli._models import Comment, Issue, priority_label


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
    click.echo("  ".join(parts))


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
