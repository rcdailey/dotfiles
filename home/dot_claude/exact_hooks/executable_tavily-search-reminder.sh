#!/usr/bin/env bash

# PostToolUse hook for tavily search tools
# Reminds Claude to use markitdown MCP instead of tavily-extract for page extraction

# Read the tool execution data from stdin
input=$(cat)

# Extract the tool name
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

# Only proceed if this was a tavily search tool
if [[ "$tool_name" =~ ^mcp__tavily__tavily-search$ ]]; then
    # Output reminder message to stdout (shown to Claude as system message)
    cat <<EOF

IMPORTANT REMINDER: To extract full content from any URLs in the search results, use the
'mcp__markitdown__convert_to_markdown' tool (NOT tavily-extract, which is blocked).
Parameter: uri (single URL string, not an array)
EOF
fi

# Always exit 0 for PostToolUse hooks (they don't block execution)
exit 0
