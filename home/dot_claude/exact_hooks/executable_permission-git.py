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

# Match: git -C <path> <subcommand> OR git <subcommand>
match = re.match(r"git\s+(?:-C\s+(?:['\"].*?['\"]|\S+)\s+)?(\S+)", command)

if match and match[1] in ALLOWED_SUBCOMMANDS:
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
