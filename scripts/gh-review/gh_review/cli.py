"""CLI argument parsing for gh-review."""

from __future__ import annotations

import argparse

from .duration import parse_duration


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gh-review",
        description="LLM-optimized PR review tool wrapping GitHub CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- view ---
    p = sub.add_parser(
        "view",
        help="view PR comments with filtering",
    )
    p.add_argument("repo", help="owner/name")
    p.add_argument("number", type=int, help="PR number")
    p.add_argument(
        "--all",
        dest="show_all",
        action="store_true",
        help="show all threads (default: unresolved only)",
    )
    p.add_argument(
        "--unanswered",
        action="store_true",
        help="only threads where PR author has not replied last",
    )
    p.add_argument(
        "--since",
        type=parse_duration,
        metavar="DURATION",
        help="relative time filter (e.g. 1h, 2d, 1w)",
    )
    p.add_argument(
        "--no-bots",
        action="store_true",
        help="drop bot comments entirely",
    )
    p.add_argument(
        "--max-body",
        type=int,
        default=500,
        metavar="N",
        help="max comment body length (default: 500)",
    )

    # --- start ---
    p = sub.add_parser("start", help="start a pending review")
    p.add_argument("repo", help="owner/name")
    p.add_argument("number", type=int, help="PR number")

    # --- delete ---
    p = sub.add_parser("delete", help="delete a pending review")
    p.add_argument(
        "review_id",
        metavar="REVIEW_ID",
        help="PRR_... node id",
    )

    # --- comment ---
    p = sub.add_parser(
        "comment",
        help="add inline comment to pending review",
    )
    p.add_argument("repo", help="owner/name")
    p.add_argument("number", type=int, help="PR number")
    p.add_argument("--review-id", required=True, help="PRR_... node id")
    p.add_argument("--path", required=True, help="file path in the PR")
    p.add_argument(
        "--line",
        type=int,
        required=True,
        help="line number (or end line for multi-line)",
    )
    p.add_argument(
        "--start-line",
        type=int,
        help="start line for multi-line comments",
    )
    p.add_argument("--body", required=True, help="comment body")
    p.add_argument(
        "--side",
        choices=["LEFT", "RIGHT"],
        default="RIGHT",
        help="diff side (default: RIGHT)",
    )
    p.add_argument(
        "--start-side",
        choices=["LEFT", "RIGHT"],
        help="diff side for start line",
    )

    # --- reply ---
    p = sub.add_parser(
        "reply",
        help="reply to a review comment thread",
    )
    p.add_argument("repo", help="owner/name")
    p.add_argument("number", type=int, help="PR number")
    p.add_argument("comment_id", type=int, help="comment database ID")
    p.add_argument("--body", required=True, help="reply body")

    return parser
