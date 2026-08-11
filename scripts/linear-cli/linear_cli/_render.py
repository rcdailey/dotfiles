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


def echo_comment(comment: Comment) -> None:
    """Print one issue comment."""
    click.echo(f"[{comment.created_at}] {comment.user_name}: {comment.body}")
