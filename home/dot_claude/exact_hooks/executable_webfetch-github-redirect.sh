#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract tool_name and url using jq (or basic grep if jq not available)
if command -v jq >/dev/null 2>&1; then
  tool_name=$(echo "$input" | jq -r '.tool_name // empty')
  url=$(echo "$input" | jq -r '.tool_input.url // empty')
else
  # Fallback to grep/sed if jq not available
  tool_name=$(echo "$input" | grep -o '"tool_name":"[^"]*"' | sed 's/"tool_name":"\([^"]*\)"/\1/')
  url=$(echo "$input" | grep -o '"url":"[^"]*"' | sed 's/"url":"\([^"]*\)"/\1/')
fi

# Only process WebFetch tools
if [[ "$tool_name" != "WebFetch" ]] || [[ -z "$url" ]]; then
  exit 0
fi

# Check if URL is a GitHub repository URL
if [[ "$url" =~ ^https?://github\.com/[^/]+/[^/]+(/.*)?$ ]]; then
  # Extract owner/repo from URL
  owner_repo=$(echo "$url" | sed -n 's|^https\?://github\.com/\([^/]\+/[^/]\+\).*|\1|p')

  echo "WebFetch blocked for GitHub repository: $owner_repo" >&2
  echo "Use GitHub MCP tools (PRIORITY 1) or 'gh' CLI for list operations only." >&2

  # Exit code 2 blocks tool call and shows stderr to Claude
  exit 2
fi

# Allow non-GitHub URLs
exit 0
