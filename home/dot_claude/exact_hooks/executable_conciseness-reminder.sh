#!/usr/bin/env bash

# UserPromptSubmit hook to remind Claude about conciseness requirements
# Fires when user submits a prompt to keep the directive in active context

cat <<EOF
REMINDER: Keep conversational responses to 4 lines maximum. No preambles/postambles/wrapper phrases.
EOF

exit 0
