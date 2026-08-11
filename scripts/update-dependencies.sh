#!/usr/bin/env zsh

set -euo pipefail

sync_environment=0

if (( $# > 1 )) || (( $# == 1 )) && [[ $1 != "--sync" ]]; then
    print -u2 "Usage: ${0:t} [--sync]"
    exit 2
fi

if (( $# == 1 )); then
    sync_environment=1
fi

repo_root=${0:A:h:h}

if [[ ! -d "$repo_root/.git" ]]; then
    print -u2 "Repository root not found: $repo_root"
    exit 1
fi

if ! (( $+commands[pre-commit] )) || ! (( $+commands[uv] )); then
    print -u2 "This script requires pre-commit and uv. Install them with mise first."
    exit 1
fi

manifests=("${(@f)$(git -C "$repo_root" ls-files -- '*pyproject.toml')}")
changed_files=("$repo_root/.pre-commit-config.yaml")

for manifest in "${manifests[@]}"; do
    changed_files+=("$repo_root/${manifest:h}/uv.lock")
done

typeset -A before_hashes

for changed_file in "${changed_files[@]}"; do
    before_hashes[$changed_file]=$(git hash-object "$changed_file")
done

pre-commit autoupdate

for manifest in "${manifests[@]}"; do
    project="$repo_root/${manifest:h}"
    print "Updating $manifest"
    (
        builtin cd "$project"
        uv lock --upgrade
        if (( sync_environment )); then
            uv sync
        fi
    )
done

updated_files=()

for changed_file in "${changed_files[@]}"; do
    if [[ ${before_hashes[$changed_file]} != "$(git hash-object "$changed_file")" ]]; then
        updated_files+=("${changed_file#$repo_root/}")
    fi
done

if (( ${#updated_files} == 0 )); then
    print "No dependency files changed."
    exit 0
fi

print "\nUpdated dependency files:"
printf '  %s\n' "${updated_files[@]}"
print "Review with: git diff -- ${updated_files[*]}"
