#!/usr/bin/env bash

#IFS=':' read -ra treeish <<< "$1"

filename=$(basename "$2")
tempfile=$(mktemp -t "git-open.XXXX.$filename") || exit 1

if git show "$1:$2" >"$tempfile"; then
  code "$tempfile"
fi

rm "$tempfile"
