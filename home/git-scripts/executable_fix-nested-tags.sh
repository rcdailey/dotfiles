#!/usr/bin/env bash
set -e

git tag -l | while read tag_name; do
    tag_type=$(git cat-file -t $tag_name)

    # Only process annotated tags
    if [[ "$tag_type" == "tag" ]]; then
        parent_hash="$(git cat-file tag $tag_name | head -n 1 | cut -d' ' -f2 -)"
        parent_type="$(git cat-file -t $parent_hash)"

        # This annotated tag points to another tag object. Recreate the tag to
        # point directly to the respective commit object instead.
        if [[ "$parent_type" == "tag" ]]; then
            echo "Fixing tag: $tag_name"
            tag_msg="$(git tag -l --format='%(contents)' $tag_name)"
            git tag -f -m "$tag_msg" $tag_name "${tag_name}^{}"
        fi
    fi
done
