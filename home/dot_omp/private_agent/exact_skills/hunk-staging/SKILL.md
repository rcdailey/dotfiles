---
name: hunk-staging
description: >-
  Use when a commit must include only selected hunks from a changed file, including commits that
  mix partial files with whole files. Do not use for ordinary whole-file or directory commits.
---

# Hunk staging

Use this only when whole-path staging would mix independently reviewable changes.

1. Inspect a nonempty index with `git diff --cached`; preserve user-staged content unless the user
   requests otherwise.
2. For an untracked file, run `git add -N -- <path>` so its hunks become selectable.
3. Run `git hunks list`, then stage quoted IDs with `git hunks add '<id>'...`.
4. Stage any complete files with `git add -- <paths>`.
5. Verify the complete staged result with `git diff --cached`.
6. Run `commit save` without paths. Paths would reset the index and discard the partial selection.

Hunk IDs remain stable while other hunks are staged, but not after editing the worktree. A failed
multi-hunk add may stage earlier requested hunks, so always perform the final verification.
