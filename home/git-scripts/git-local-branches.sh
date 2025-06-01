#!/usr/bin/env bash
set -e

branches="$(git for-each-ref --sort=committerdate --format='%(refname:short)' refs/heads/)"
remote_branches="$(git for-each-ref --format='%(refname:short)' refs/remotes/origin/)"

# echo "Local branches with no correspondingly named upstream branch on origin:"
# echo "---------------------"

while IFS= read -r branch; do
    if ! grep -Fxq "origin/$branch" <<< "$remote_branches"; then
        echo "$branch"
    fi
done <<< "$branches"
