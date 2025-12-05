#!/usr/bin/env bash

# UserPromptSubmit hook: conciseness reminder + context7 check + CWD display
set -euo pipefail

# Read stdin (required for all hooks)
input=$(cat)

# Always show conciseness reminder
echo "REMINDER: Keep conversational responses to 4 lines maximum. No preambles/postambles/wrapper phrases."
echo "NEVER use markdown tables in conversational responses - use bullet lists instead."

# Context7 check (only if mentioned in prompt)
if echo "$input" | rg -qi "context7"; then
    echo "REQUIRED: Use Context7 website docs (e.g. /websites/* library IDs) instead of github-based results (e.g. /org/repo)"
fi

echo "CRITICAL: File paths mentioned with @ are relative to session start directory"
