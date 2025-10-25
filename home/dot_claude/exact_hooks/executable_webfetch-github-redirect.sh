#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract tool_name and URL/URI using jq (or basic grep if jq not available)
if command -v jq >/dev/null 2>&1; then
  tool_name=$(echo "$input" | jq -r '.tool_name // empty')
  uri=$(echo "$input" | jq -r '.tool_input.uri // empty')
  urls=$(echo "$input" | jq -r '.tool_input.urls[]? // empty')
else
  # Fallback to grep/sed if jq not available
  tool_name=$(echo "$input" | grep -o '"tool_name":"[^"]*"' | sed 's/"tool_name":"\([^"]*\)"/\1/')
  uri=$(echo "$input" | grep -o '"uri":"[^"]*"' | sed 's/"uri":"\([^"]*\)"/\1/')
  urls=$(echo "$input" | grep -o '"urls":\["[^"]*"' | sed 's/"urls":\["\([^"]*\)"/\1/')
fi

# Only process markitdown and tavily-extract tools
if [[ "$tool_name" != "mcp__markitdown__convert_to_markdown" ]] && [[ "$tool_name" != "mcp__tavily__tavily-extract" ]]; then
  exit 0
fi

# Determine which URL to check based on tool
if [[ "$tool_name" == "mcp__markitdown__convert_to_markdown" ]]; then
  target_url="$uri"
elif [[ "$tool_name" == "mcp__tavily__tavily-extract" ]]; then
  target_url="$urls"
fi

# Skip if no URL to check
if [[ -z "$target_url" ]]; then
  exit 0
fi

# Check if URL is a GitHub repository or raw content URL
if [[ "$target_url" =~ ^https?://(github\.com|raw\.githubusercontent\.com)/[^/]+/[^/]+(/.*)?$ ]]; then
  echo "Error: Do not use $tool_name against GitHub repositories" >&2
  echo "Use native GitHub integration tools instead." >&2

  # Exit code 2 blocks tool call and shows stderr to Claude
  exit 2
fi

# Allow non-GitHub URLs
exit 0
