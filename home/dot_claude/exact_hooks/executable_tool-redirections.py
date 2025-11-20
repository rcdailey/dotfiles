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
        "find . -maxdepth 2 -type d | rg pattern",
        "find /usr -type f | grep config",
        "rg files | grep -v '/obj/'",
        "cat file | grep pattern",
        "ls | grep -E '^test'",
        "ls -la | rg blocky",
        "ls *.txt | grep file",
        "rg pattern | grep other",
        "rg --files | grep filter",
        "sops --set file.yaml key value",
        # Should NOT match any patterns (excluded commands)
        "git commit -m 'find the right solution'",
        "ssh user@host 'grep logs'",
        "kubectl exec -n media restore-config -- grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini",
        "kubectl exec -n media restore-config -- sh -c \"rg 'api_key|download_dir|complete_dir' /config/sabnzbd.ini || grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini\"",
        "docker exec container grep pattern file",
        "podman exec container find /path -name '*.txt'",
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

    # Test command exclusion logic
    print("=== Command Exclusion Testing ===")
    test_exclusion_commands = [
        "kubectl exec -n media restore-config -- grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini",
        "kubectl exec -n media restore-config -- sh -c \"rg 'api_key|download_dir|complete_dir' /config/sabnzbd.ini || grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini\"",
        "docker exec container grep pattern file",
        "podman exec container find /path -name '*.txt'",
        "ssh user@host 'grep logs'",
        "git commit -m 'find the right solution'",
        "grep pattern file.txt",  # Should be blocked
        "find /path -name '*.txt'",  # Should be blocked
    ]

    for cmd in test_exclusion_commands:
        is_excluded = bool(
            re.match(r"^\s*(git|ssh|kubectl\s+exec|docker\s+exec|podman\s+exec)\s", cmd)
        )
        would_match = any(rule.pattern.search(cmd) for rule in REDIRECTIONS)
        status = (
            "EXCLUDED" if is_excluded else ("BLOCKED" if would_match else "ALLOWED")
        )
        print(f"  {cmd[:50]}{'...' if len(cmd) > 50 else ''}: {status}")

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

    # Block LS tool - require rg instead
    if tool_name == "LS":
        error_msg = "TOOL USAGE VIOLATION: Use 'rg --files' or 'rg --files -g pattern' instead of LS tool for file listing"
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    # Block Search tool - require rg instead
    if tool_name == "Search":
        error_msg = 'TOOL USAGE VIOLATION: Use \'rg\' instead of Search tool for content searching\nExamples: rg "pattern", rg -i "pattern" (case insensitive), rg "pattern" --type js (file type), rg -A3 -B3 "pattern" (with context)'
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    # Process Bash commands
    if tool_name == "Bash" and command:
        # Skip validation for remote execution and container commands to avoid false positives
        if re.match(
            r"^\s*(git|ssh|kubectl\s+(exec|run|debug)|docker\s+exec|podman\s+exec)\s",
            command,
        ):
            sys.exit(0)

        # Check each redirection pattern
        for rule in REDIRECTIONS:
            if rule.pattern.search(command):
                error_msg = f"TOOL USAGE VIOLATION: {rule.message}"
                print(error_msg, file=sys.stderr)
                sys.exit(2)


if __name__ == "__main__":
    main()
