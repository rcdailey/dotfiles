#!/usr/bin/env bash
# Show current working directory to Claude after each Bash command
set -euo pipefail

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Current directory: $(pwd)"
  }
}
EOF
