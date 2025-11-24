#!/usr/bin/env bash

# SessionStart hook that establishes critical directives at session initialization
#
# PURPOSE:
#   Displays key tool usage rules once at session start to proactively guide
#   Claude before violations occur. Acts as a "session primer" that reinforces
#   critical patterns enforced by PreToolUse hooks.
#
# WHEN IT RUNS:
#   Executes once when a new Claude Code session begins (not on every prompt).
#   This is the appropriate hook for initialization messages that only need to
#   be shown once.
#
# WHY IT READS STDIN:
#   SessionStart hooks receive JSON data about the session initialization.
#   Currently unused but required - hooks must consume stdin to prevent blocking.
#   Future enhancement could parse session data to conditionally display messages.

# Read stdin JSON data (contains session initialization information)
# Currently unused but required - hooks must consume stdin
input=$(cat)

# Output static session directives (shown to Claude as system message)
cat <<EOF
SESSION DIRECTIVES - CRITICAL TOOL USAGE RULES:

BASH COMMANDS:
- MUST use 'rg' instead of 'grep' (all scenarios)
- MUST use 'rg --files -g "pattern"' instead of 'find -name'
- NEVER chain: 'ls | rg', 'find | rg', 'rg | grep'
- NEVER use LS or Search tools (blocked - use rg instead)

These rules are enforced by PreToolUse hooks that will block violations.

CRITICAL: Session Start Directory: $(pwd)
EOF

# Always exit 0 for prompt hooks
exit 0
