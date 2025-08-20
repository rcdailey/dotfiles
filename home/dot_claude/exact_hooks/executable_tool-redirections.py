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
        pattern=re.compile(r"\bls\b.*\|.*\b(rg|grep)\b"),
        message="Use 'rg --files -g pattern' instead of 'ls | rg/grep' for file filtering",
        examples=["ls -la | rg pattern", "ls *.txt | grep file"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\bfind\b.*\|.*\b(rg|grep)\b"),
        message="Use 'rg --files -g pattern' instead of 'find | rg/grep' combinations",
        examples=[
            "find . -type d | rg pattern",
            "find /path -name '*.txt' | grep filter",
        ],
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

# Tavily MCP restrictions
TAVILY_RESTRICTIONS = []


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
        "find . -maxdepth 2 -type d | rg pattern",
        "find /usr -type f | grep config",
        "rg files | grep -v '/obj/'",
        "cat file | grep pattern",
        "ls | grep -E '^test'",
        "ls -la | rg blocky",
        "ls *.txt | grep file",
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

    # Test Tavily queries and URLs
    tavily_test_queries = [
        # Should match GitHub pattern (repositories)
        "search github.com repositories",
        "find issues on GitHub.com",
        "https://github.com/user/repo",
        "https://github.com/actions/checkout",
        # Should NOT match (docs.github.com)
        "https://docs.github.com/en/actions/how-tos/sharing-automations/reusing-workflows",
        "https://docs.github.com/en/github/getting-started-with-github",
        "search for python tutorials",
        "find documentation online",
        "https://stackoverflow.com/questions",
    ]

    print("=== Tavily Restrictions ===")
    for i, rule in enumerate(TAVILY_RESTRICTIONS, 1):
        print(f"=== Tavily Rule {i}: {rule.pattern.pattern} ===")
        print(f"Examples: {', '.join(rule.examples)}")

        matches = [query for query in tavily_test_queries if rule.pattern.search(query)]
        non_matches = [
            query for query in tavily_test_queries if not rule.pattern.search(query)
        ]

        if matches:
            print("MATCHES:")
            for query in matches:
                print(f"  {query}")

        if non_matches:
            print("  No matches:")
            for query in non_matches:
                print(f"  {query}")

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

    # Process Bash commands
    if tool_name == "Bash" and command:
        # Skip validation for git and ssh commands to avoid false positives
        if re.match(r"^\s*(git|ssh)\s", command):
            sys.exit(0)

        # Check each redirection pattern
        for rule in REDIRECTIONS:
            if rule.pattern.search(command):
                error_msg = f"TOOL USAGE VIOLATION: {rule.message}"
                print(error_msg, file=sys.stderr)
                sys.exit(2)

    # Process Tavily MCP tools
    elif tool_name.startswith("mcp__tavily__"):
        query = input_data.get("tool_input", {}).get("query", "")
        urls = input_data.get("tool_input", {}).get("urls", [])

        # Check query for GitHub references
        if query:
            for rule in TAVILY_RESTRICTIONS:
                if rule.pattern.search(query):
                    error_msg = f"TAVILY USAGE VIOLATION: {rule.message}"
                    print(error_msg, file=sys.stderr)
                    sys.exit(2)

        # Check URLs for GitHub references
        if urls:
            for url in urls:
                for rule in TAVILY_RESTRICTIONS:
                    if rule.pattern.search(url):
                        error_msg = f"TAVILY USAGE VIOLATION: {rule.message}"
                        print(error_msg, file=sys.stderr)
                        sys.exit(2)


if __name__ == "__main__":
    main()
