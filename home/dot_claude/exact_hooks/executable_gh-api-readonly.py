#!/usr/bin/env python3

"""
PreToolUse hook for Claude Code to block mutating gh api operations.
Only allows read-only gh api commands (without -X flag or with -X GET).
"""

import json
import re
import sys


def main() -> None:
    """Block gh api commands with mutating HTTP methods."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    command = input_data.get("tool_input", {}).get("command", "")

    if tool_name != "Bash" or not command:
        sys.exit(0)

    # Check if this is a gh api command
    if not re.search(r"\bgh\s+api\b", command):
        sys.exit(0)

    # Check for -X flag with mutating method
    mutating_pattern = re.compile(r"-X\s+(POST|PUT|PATCH|DELETE)\b", re.IGNORECASE)

    if mutating_pattern.search(command):
        error_msg = (
            "GH API VIOLATION: Mutating operations not allowed. "
            "gh api with -X POST/PUT/PATCH/DELETE is blocked. "
            "Only read-only operations (GET or no -X flag) are permitted."
        )
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
