#!/usr/bin/env bash
#want="$(git rev-parse --verify "$1")"
#git rev-list --all | while read commit ; do
#    git ls-tree -r $commit | while read perm type hash filename; do
#        if test "$want" = "$hash"; then
#            echo matched $filename in commit $commit
#        fi
#    done
#done

#obj_name="$(git rev-parse --verify "$1")"
#git log --all --pretty=format:%H \
#| xargs -n1 -I% sh -c "git ls-tree % -- $obj_name | grep -q $obj_name && echo %"

obj_name="$(git rev-parse --verify "$1")"
shift
git log "$@" --all --pretty=format:'%T %h %s' \
| while read tree commit subject ; do
    if git ls-tree -r $tree | grep -q "$obj_name" ; then
        echo $commit "$subject"
    fi
done
