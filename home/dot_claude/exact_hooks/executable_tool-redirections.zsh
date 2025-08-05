#!/usr/bin/env zsh

# Consolidated tool redirection hook
# Catches common tool usage patterns and suggests better alternatives

# Tool redirection rules: pattern -> message
local -A redirections=(
    "^[[:space:]]*grep"
    "Use 'rg' (ripgrep) instead of 'grep' for better performance and features"

    "find[[:space:]]+[^[:space:]]+[[:space:]]+-name"
    "Use 'rg --files -g pattern' or 'rg pattern --glob pattern' instead of 'find -name'"

    "sops[[:space:]]+--set"
    "Use 'sops set' instead of 'sops --set'\nCorrect: sops set file.sops.yaml '[\"section\"][\"key\"]' '\"value\"'"
)

# Parse JSON input
local json_input=$(cat)
local tool_name=$(echo "$json_input" | jq -r '.tool_name // ""')
local command=$(echo "$json_input" | jq -r '.tool_input.command // ""')

# Only process Bash commands
[[ "$tool_name" == "Bash" && -n "$command" ]] || exit 0

# Skip validation for git and ssh commands to avoid false positives
if [[ $command =~ ^[[:space:]]*(git|ssh)[[:space:]] ]]; then
    exit 0
fi

# Check each redirection pattern
for pattern message in ${(kv)redirections}; do
    if [[ $command =~ $pattern ]]; then
        print -u2 "• $message"
        exit 2
    fi
done
