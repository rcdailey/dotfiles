#!/usr/bin/env python3
"""Auto-allow git -C <path> <subcommand> when subcommand is in allowed list."""

import json
import re
import sys

ALLOWED_SUBCOMMANDS = {
    "add",
    "branch",
    "diff",
    "log",
    "ls-tree",
    "mv",
    "reflog",
    "rev-parse",
    "rm",
    "show",
    "status",
}

data = json.load(sys.stdin)
if data.get("tool_name") != "Bash":
    sys.exit(0)

command = data.get("tool_input", {}).get("command", "")

# Find ALL git subcommands in the command (handles chained commands like && or ;)
GIT_PATTERN = re.compile(r"git\s+(?:-C\s+(?:['\"].*?['\"]|\S+)\s+)?(\S+)")
matches = GIT_PATTERN.findall(command)

# Only auto-allow if ALL git subcommands are in the allowed list
if matches and all(subcmd in ALLOWED_SUBCOMMANDS for subcmd in matches):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"},
                }
            }
        )
    )
