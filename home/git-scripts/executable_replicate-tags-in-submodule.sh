#!/usr/bin/env bash
#set -x

#DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
#python "$DIR/replicate-tags-in-submodule.py" "$@"

submodule="$1"
tag_prefix="$2"

if [[ -z "$submodule" || -z "$tag_prefix" ]]; then
    echo "Usage: replicate-tags-in-submodule.sh [submodule_path] [tag_prefix]"
    exit 1
fi

for tag in $(git tag -l); do

    # If cat-file identifies the submodule as a tree, that means it isn't a
    # submodule, and we should skip this tag.
    git cat-file -t "$tag:$submodule" > /dev/null 2>&1 && continue

    sha1="$(git rev-parse "$tag:$submodule")"
    tag="${tag_prefix:+${tag_prefix}/}${tag}"
    pushd "$submodule" > /dev/null || return

    # Check if the tag already exists and points to this SHA1
    existing_tag="$(git rev-parse $tag 2> /dev/null)"
    if [[ "$existing_tag" != "$sha1" ]]; then
        echo ">> Creating submodule tag for: $tag"
        git tag -f "$tag" "$sha1"
    fi
    popd > /dev/null || return
done
