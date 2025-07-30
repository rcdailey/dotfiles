#!/usr/bin/env bash
#set -ex

# $1 = remote name
# $2 = optional revision on branch
# $@ = Additional arguments to push (e.g. --force)

remoteName="$1"
shift
pushRev="${1:-HEAD}"
shift
branchName="$(git rev-parse --symbolic-full-name HEAD)"

git push "$remoteName" "${pushRev}:${branchName}" "$@"
