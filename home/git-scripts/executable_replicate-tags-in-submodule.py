import sys, os
from git import Repo
from git.exc import GitCommandError
import os.path as osp

if len(sys.argv) != 3:
    print("Usage: replicate-tags-in-submodule.sh [submodule_path] [tag_prefix]")
    exit(1)

submodule_path = sys.argv[1]
tag_prefix = sys.argv[2]

repo = Repo(Repo.working_dir)
submodule = Repo(submodule_path)


def CreateSubmoduleTag(tag, commit):
    submodule_tag = '{}/{}'.format(tag_prefix, tag)

    for tag in submodule.tags:
        if tag == submodule_tag and tag.commit == commit:
            print('Tag already exists: ' + submodule_tag)
            return

    submodule.create_tag(submodule_tag, commit, 'Auto generated tag')

for tag in repo.tags:
    try:
        commit_hash = repo.git.rev_parse('{}:{}'.format(tag.name, submodule_path))
        CreateSubmoduleTag(str(tag), str(tag.commit))
        print("{}: {}".format(tag, commit_hash))
        break
    except GitCommandError as e:
        print("Exception: {}".format(str(e)))




#submodule="$1"
#tag_prefix="$2"
#
#if [[ -z "$submodule" || -z "$tag_prefix" ]]; then
#    echo "Usage: replicate-tags-in-submodule.sh [submodule_path] [tag_prefix]"
#    exit 1
#fi
#
#for tag in $(git tag -l); do
#    sha1="$(git rev-parse "$tag:$submodule")"
#    tag="${tag_prefix:+${tag_prefix}/}${tag}"
#    pushd "$submodule" > /dev/null
#
#    # Check if the tag already exists and points to this SHA1
#    existing_tag="$(git rev-parse $tag 2> /dev/null)"
#    if [[ "$existing_tag" != "$sha1" ]]; then
#        echo ">> Creating submodule tag for: $tag"
#        git tag -f "$tag" "$sha1"
#    fi
#    popd > /dev/null
#done
