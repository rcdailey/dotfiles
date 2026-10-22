#!/usr/bin/env bash

set -euo pipefail

sync_environment=0

if (( $# > 1 )) || { (( $# == 1 )) && [[ $1 != "--sync" ]]; }; then
    echo "Usage: $(basename "$0") [--sync]" >&2
    exit 2
fi

if (( $# == 1 )); then
    sync_environment=1
fi

repo_root=$(dirname "$(dirname "$(realpath "$0")")")

if [[ ! -d "$repo_root/.git" ]]; then
    echo "Repository root not found: $repo_root" >&2
    exit 1
fi

if ! command -v pre-commit >/dev/null || ! command -v uv >/dev/null; then
    echo "This script requires pre-commit and uv. Install them with mise first." >&2
    exit 1
fi

mapfile -t manifests < <(git -C "$repo_root" ls-files -- '*pyproject.toml')
changed_files=("$repo_root/.pre-commit-config.yaml")

for manifest in "${manifests[@]}"; do
    changed_files+=("$repo_root/$(dirname "$manifest")/uv.lock")
done

declare -A before_hashes

for changed_file in "${changed_files[@]}"; do
    before_hashes[$changed_file]=$(git hash-object "$changed_file")
done

pre-commit autoupdate

for manifest in "${manifests[@]}"; do
    project="$repo_root/$(dirname "$manifest")"
    echo "Updating $manifest"
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
        updated_files+=("${changed_file#"$repo_root"/}")
    fi
done

if (( ${#updated_files[@]} == 0 )); then
    echo "No dependency files changed."
    exit 0
fi

printf '\nUpdated dependency files:\n'
printf '  %s\n' "${updated_files[@]}"
echo "Review with: git diff -- ${updated_files[*]}"
