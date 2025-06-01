#!/usr/bin/env bash

#IFS=':' read -ra treeish <<< "$1"

filename=$(basename "$2")
tempfile=$(mktemp -t "git-open.XXXX.$filename") || exit 1

git show "$1:$2" > "$tempfile"

if [[ $? -eq 0 ]]; then
    code "$tempfile"
fi

rm "$tempfile"
