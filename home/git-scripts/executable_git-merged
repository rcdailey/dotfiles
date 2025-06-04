#!/usr/bin/env bash
remote="${1:-origin}"
branch="$2"
git branch -r --list "$remote/*" --merged $branch \
    | sed "s/\s*$remote\///" \
    | egrep -v "^(HEAD|release|hotfix|master|develop)"
