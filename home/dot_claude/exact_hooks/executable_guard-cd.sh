#!/usr/bin/env bash
# Guard against cd commands to prevent directory navigation confusion
set -euo pipefail

payload="$(cat)"
tool="$(jq -r '.tool_name // ""' <<<"$payload")"
cmd="$(jq -r '.tool_input.command // ""' <<<"$payload")"

# Only inspect Bash tool calls
[[ "$tool" == "Bash" ]] || exit 0
[[ -n "$cmd" ]] || exit 0

# Block actual cd commands but avoid false positives in strings/arguments
# This regex matches cd as a standalone command at word boundaries
if grep -Eq '(^|[;&|()[:space:]])cd([[:space:]]|;|&|\||$)' <<<"$cmd" && \
   ! grep -Eq '(git|gh|npm|yarn|make|cmake|docker).*-[a-zA-Z]*[cC].*' <<<"$cmd" && \
   ! grep -Eq '"[^"]*cd[^"]*"' <<<"$cmd" && \
   ! grep -Eq "'[^']*cd[^']*'" <<<"$cmd"; then
  {
    echo "Blocked: never use plain 'cd'."
    echo "Rewrite using either:"
    echo "  ( cd \"/abs/path\" && full_command )"
    echo "  or a tool flag: git -C \"/abs/path\" … / yarn --cwd \"/abs/path\" … / make -C \"/abs/path\" …"
  } 1>&2
  exit 2
fi
