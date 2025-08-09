#!/usr/bin/env zsh

# Read JSON input from stdin
input=$(cat)

# Extract values from JSON
model_name=$(echo "$input" | jq -r '.model.display_name')
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')

# Get directory name
dir_name=$(basename "$current_dir")

# Check if we're in a git repository and get branch
cd "$current_dir" 2>/dev/null
if git rev-parse --git-dir >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null || echo "detached")
    # Format and output the status line with colors, including git info
    printf "[\e[34m%s\e[0m] 📁 \e[33m%s\e[0m | \e[32m🌿 %s\e[0m" "$model_name" "$dir_name" "$branch"
else
    # Format and output the status line with colors, no git info
    printf "[\e[34m%s\e[0m] 📁 \e[33m%s\e[0m" "$model_name" "$dir_name"
fi
