#!/usr/bin/env bash
# set -x

# To help misuse of the command, error out if we get more or less than 1 argument.
# Print help information as well.
if (($# != 1)); then
  echo "Invalid Arguments"
  echo "Usage: git nuke [branch|tag]"
  exit 1
fi

input_ref="$1"

if [[ "$input_ref" == "-" ]]; then
  input_ref="@{-1}"
fi

ref="$(git rev-parse --symbolic-full-name "$input_ref" 2>/dev/null)"
case "$ref" in
refs/heads/*)
  ref=${ref#refs/heads/}
  type="branch"
  ;;
refs/tags/*)
  ref=${ref#refs/tags/}
  type="tag"
  ;;
refs/remotes/*)
  ref=${ref#refs/remotes/*/}
  type="branch"
  ;;
*)
  echo >&2 "That's not a branch or tag: $input_ref"
  exit 1
  ;;
esac

while true; do
  read -r -n1 -p "Delete $type '$ref'? [y/n]: " yn
  case $yn in
  [Yy]*) break ;;
  [Nn]*) exit ;;
  *) echo "Please answer yes or no." ;;
  esac
done

echo # Insert newline after user input

delete_branch() {
  remote="$1"

  # If a remote is specified, delete the remote branch or tag
  if [[ -n "$remote" ]]; then
    case "$type" in
    branch) results="$(git show-ref "$remote/$ref")" ;;
    tag) results="$(git ls-remote --tags origin | grep "tags/$ref")" ;;
    esac

    if [[ -n "$results" ]]; then
      echo "> Deleting remote $type on $remote"
      git push --delete "$remote" "$ref"
    fi
  # Otherwise it is a local branch (or tag)
  else
    if [[ -n "$(git show-ref "$ref")" ]]; then
      echo "> Deleting local $type"
      case "$type" in
      branch) deleteOption="-D" ;;
      tag) deleteOption="-d" ;;
      esac
      git $type "$deleteOption" "$ref"
    fi
  fi
}

delete_branch origin
delete_branch fork
delete_branch
