#!/usr/bin/env bash

# $1 = remote name
# $2 = branch name

ref=$(git rev-parse --symbolic-full-name "$2") &&
  case "$ref" in
  '')
    echo >&2 "No such thing: $2"
    exit 1
    ;;
  refs/heads/*) ref=${ref#refs/heads/} ;;
  *)
    echo >&2 "That's not a branch: $2"
    exit 2
    ;;
  esac &&
  git push "$1" HEAD ":refs/heads/$ref" &&
  git branch -D "$ref"
