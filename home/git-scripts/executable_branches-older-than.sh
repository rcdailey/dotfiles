#!/usr/bin/env bash
age=$1
refpattern=${2:-refs/heads}

git for-each-ref \
  --sort=-committerdate \
  --format="%(committerdate:short) %(refname:short)" "$refpattern" \
| awk "\$0 <= \"$(date --date="-$age months" +'%Y-%m-%d')\""

# if [[ "$remote" != "" ]]; then
#     branch_list=$(git branch -r --list "$remote/*" | grep -v HEAD | sed "s/\* //")
# else
#     branch_list=$(git branch --list | grep -v HEAD | sed "s/\* //")
# fi

# for k in $branch_list; do
#   if [[ -z "$(git log -1 --since="$age" -s $k)" ]]; then
#     echo "$k" | sed "s/origin\///"
#   fi
# done
