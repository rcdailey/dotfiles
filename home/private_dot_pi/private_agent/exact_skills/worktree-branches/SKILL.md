---
name: worktree-branches
description: >-
  Use when asked to work on an issue, start a branch, or rename a branch, and when starting work in
  a newly created git worktree.
---

# Worktree Branches

The user creates worktrees (worktrunk, often from herdr); never create one.

- In a linked worktree (`git rev-parse --git-dir` differs from `--git-common-dir`): confirm the
  current branch belongs to that work, then rename it to repository convention, including any issue
  key, with `git branch -m`. Worktree names stay short and need not match the branch.
- In the main checkout: ask whether to continue there or wait for the user to create a worktree.

A new linked worktree may lack the main checkout's untracked local state (installed dependencies,
env files, generated artifacts). Prepare it from knowledge of the stack. Repository instructions
supplement or override that when they apply to the worktree, even if they never mention worktrees.
