---
name: hunk-staging
description: >-
  Use when a commit must include only selected hunks or lines from a changed file, including
  commits that mix partial files with whole files, or when unstaging part of the index. Do not use
  for ordinary whole-file or directory commits.
---

# Hunk staging

Stage partial files with `git-surgeon`, which addresses hunks by ID without prompts. Never edit the
worktree to shape a commit; select lines instead. Run `git-surgeon <command> --help` for syntax.

1. Inspect a nonempty index with `git diff --cached`; preserve user-staged content unless the user
   requests otherwise.
2. Mark untracked files so their hunks become selectable:
   `git ls-files -z --others --exclude-standard -- <paths> | xargs -0 git add -N --`. Do not run
   `git add -N .`; it also stages tracked deletions.
3. List candidates with `git-surgeon hunks --file <path>` (omit `--file` only for small diffs). Each
   hunk header starts with a 7-hex ID, followed by indented diff lines; filter headers with
   `rg '^[0-9a-f]{7} '` for a compact list. Headers show only the enclosing context, so confirm
   which hunk is which with `show <id>` rather than by list order.
4. Stage whole hunks with `git-surgeon stage <id>...`.
5. For part of a hunk, run `git-surgeon show <id>` (or `hunks --file <path> --full` to number every
   hunk in one call) and stage with `--lines START-END`. Line numbers are hunk-relative and count
   context lines, not only changed lines. `--lines` takes one range.
6. Stage complete files with `git add -- <paths>` and deletions with `git add -u -- <paths>`.
7. Verify the complete staged result with `git diff --cached`, and the remainder with `git diff`.
8. Commit without paths (for example `commit save` with no paths); paths reset the index and discard
   the partial selection.

IDs are content hashes of path and hunk text; identical hunks get `-2`, `-3` suffixes, and an
unknown ID means the listing is stale. Untouched hunks keep their IDs while others are staged or
committed, so one listing serves a series of commits; re-list after staging part of a hunk or
editing a file, because the remainder's ID can change. Do not assume a multi-ID `stage` is
all-or-nothing; step 7 catches a partial result. After an interrupted or failed staging command,
unstage your selection with `git reset -- <paths>` and re-mark untracked files before retrying. Undo
a wrong selection with `git-surgeon unstage <id>` from `git-surgeon hunks --staged`.
