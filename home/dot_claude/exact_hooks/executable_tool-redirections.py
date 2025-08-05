#!/usr/bin/env python3

"""
Consolidated tool redirection hook for Claude Code.
Catches common tool usage patterns and suggests better alternatives.
"""

import json
import re
import sys
from typing import NamedTuple


class RedirectionRule(NamedTuple):
    """A single redirection rule with pattern and message."""

    pattern: re.Pattern[str]
    message: str
    examples: list[str]


# Tool redirection rules
REDIRECTIONS = [
    RedirectionRule(
        pattern=re.compile(r"\bgrep\b"),
        message="Use 'rg' instead of 'grep' for better performance and features",
        examples=["grep pattern file.txt", "ps aux | grep process"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\bfind\b.*-name"),
        message="Use 'rg --files -g pattern' instead of 'find -name'",
        examples=["find /path -name '*.txt'", "find . -name 'test*'"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\|.*\bgrep\b"),
        message="Avoid chaining grep commands - use 'rg' with multiple patterns or combined regex",
        examples=["rg files | grep -v '/obj/'", "cat file | grep pattern"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\brg\b.*\|.*(grep|rg)\b"),
        message="Avoid chaining rg/grep - use single 'rg' command with combined patterns or regex",
        examples=["rg pattern | rg other", "rg --files | grep filter"],
    ),
    RedirectionRule(
        pattern=re.compile(r"sops\s+--set"),
        message="Use 'sops set' instead of 'sops --set'\nCorrect: sops set file.sops.yaml '[\"section\"][\"key\"]' '\"value\"'",
        examples=["sops --set file.yaml key value"],
    ),
]


def dry_run() -> None:
    """Test all redirection patterns against sample commands."""
    print("Testing regex patterns against sample commands:\n")

    # Comprehensive test commands
    test_commands = [
        # Should match patterns
        "grep pattern file.txt",
        "ps aux | grep process",
        "grep -v unwanted file.txt",
        "find /path -name '*.txt'",
        "find . -name 'test*'",
        "rg files | grep -v '/obj/'",
        "cat file | grep pattern",
        "ls | grep -E '^test'",
        "rg pattern | rg other",
        "rg --files | grep filter",
        "sops --set file.yaml key value",
        # Should NOT match any patterns
        "git commit -m 'find the right solution'",
        "ssh user@host 'grep logs'",
        "rg files | head -10",
        "sops set file.yaml key value",
        "find /usr/local -type f",
    ]

    for i, rule in enumerate(REDIRECTIONS, 1):
        print(f"=== Rule {i}: {rule.pattern.pattern} ===")
        print(f"Examples: {', '.join(rule.examples)}")

        matches = [cmd for cmd in test_commands if rule.pattern.search(cmd)]
        non_matches = [cmd for cmd in test_commands if not rule.pattern.search(cmd)]

        if matches:
            print("✓ MATCHES:")
            for cmd in matches:
                print(f"  {cmd}")

        if non_matches:
            print("  No matches:")
            for cmd in non_matches[:3]:  # Show first 3 to keep output manageable
                print(f"  {cmd}")
            if len(non_matches) > 3:
                print(f"  ... and {len(non_matches) - 3} more")

        print()


def main() -> None:
    """Main hook logic."""
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run()
        return

    # Normal hook operation
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    command = input_data.get("tool_input", {}).get("command", "")

    # Only process Bash commands
    if tool_name != "Bash" or not command:
        sys.exit(0)

    # Skip validation for git and ssh commands to avoid false positives
    if re.match(r"^\s*(git|ssh)\s", command):
        sys.exit(0)

    # Check each redirection pattern
    for rule in REDIRECTIONS:
        if rule.pattern.search(command):
            print(f"• {rule.message}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
