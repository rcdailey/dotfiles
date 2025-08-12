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
base_status=$(printf "[\e[38;2;0;150;255m%s\e[0m] 📁 \e[38;2;255;215;0m%s\e[0m" "$model_name" "$dir_name")
if git rev-parse --git-dir >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null || echo "detached")
    printf "%s | \e[38;2;0;255;0m🌿 %s\e[0m" "$base_status" "$branch"
else
    printf "%s" "$base_status"
fi
