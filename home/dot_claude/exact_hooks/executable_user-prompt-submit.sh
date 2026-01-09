#!/usr/bin/env bash

# UserPromptSubmit hook: conciseness reminder + path resolution reminder
set -euo pipefail

# Read stdin (required for all hooks)
input=$(cat)

# Always show conciseness reminder
echo "REMINDER: Keep conversational responses to 4 lines maximum. No preambles/postambles/wrapper phrases."
echo "NEVER use markdown tables in conversational responses - use bullet lists instead."

echo "CRITICAL: File paths mentioned with @ are relative to session start directory"
