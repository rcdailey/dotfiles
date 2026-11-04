---
name: gh-stack
description: >-
  Use when creating, extending, restacking, pushing, or opening PRs for stacked branches with
  `gh stack`, or when `gh stack view` shows the current branch belongs to a stack.
---

# gh-stack

`gh stack` owns stacked branches: restacks, pushes, and GitHub's stack view. `gh pr` owns PR
content. Stack only deliberately dependent branches (built on an unmerged parent PR); branch
independent work from the default branch.

## Branches

- Adopt existing branches bottom to top with `gh stack init <parent> <child>`.
- Extend a stack by checking out its top branch and running `gh stack add <branch>`.
- Restack and push stack branches only through `gh stack`, never `git rebase` or `git push`.

## Restacking

Restack after any commit to a branch with children, and after a parent merges or the default branch
moves.

- `gh stack rebase` restacks locally without pushing; use it whenever pushing is not yet approved.
- When this session owns only part of the stack, restack only its branch (bottom:
  `gh stack rebase --downstack`; higher: `gh stack rebase --no-trunk --upstack --downstack`) and
  report which children need a restack.
- When this session owns every branch, run `gh stack sync --prune` (fetches, restacks, pushes, links
  open PRs into the stack). If its push is rejected, run `gh stack push`.

A request to open or update a stacked PR authorizes the push it needs; `gh stack` pushes with
`--force-with-lease`. Ask first only when the push would rewrite a branch another person owns or has
pushed to.

## Opening PRs

1. Push the branch with `gh stack push`.
2. Open the PR with `gh pr create --base <parent-branch>`; a matching base alone does not create
   GitHub's stack view.
3. Link the stack with `gh stack sync`, or `gh stack link <parent-PR> <child-PR>` when sync cannot
   run.

Never open PRs through `gh stack`: `submit` is denied (`--auto` writes generated titles and empty
bodies), and `link` creates PRs for branch-name arguments, so pass it PR numbers only.
