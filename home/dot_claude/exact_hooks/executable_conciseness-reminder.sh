#!/usr/bin/env bash

# PostToolUse hook to remind Claude about conciseness requirements
# Fires after every tool use to keep the directive in active context

cat <<EOF

REMINDER: Keep responses to 4 lines maximum. No preambles/postambles/wrapper phrases.
EOF

exit 0
