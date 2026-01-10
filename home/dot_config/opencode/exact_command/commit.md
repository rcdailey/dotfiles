---
description: Create git commits with conventional commit format
---

Load the `git-commit` skill, then execute a commit workflow based on arguments below. Output only
the final commit message(s).

Arguments: "$ARGUMENTS"

## Workflow

Parse $ARGUMENTS to select workflow:

- **No arguments**: Commit staged changes only. Run `git diff --cached`. Do not run git add.
- **"all"**: Run `git add -A`, then `git diff --cached`, then commit.
- **"multiple commits"**: Reset staging, analyze all changes with `git diff`, group logically by
  file type/directory/change type, commit each group separately. Aim for 2-5 commits.

If no changes exist, stop and report.
