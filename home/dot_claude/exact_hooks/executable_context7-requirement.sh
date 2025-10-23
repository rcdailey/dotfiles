#!/usr/bin/env bash

# UserPromptSubmit hook that enforces Context7 website documentation usage
# when the user mentions "context7" in their prompt

# Read JSON input from stdin
input=$(cat)

# Check if "context7" appears in the prompt (case insensitive)
if echo "$input" | rg -qi "context7"; then
    echo "REQUIRED: Use Context7 website docs (e.g. /websites/* library IDs) instead of /github/*"
fi

exit 0
