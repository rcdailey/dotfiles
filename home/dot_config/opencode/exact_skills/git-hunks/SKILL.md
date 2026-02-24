---
name: git-hunks
description: >
  Use when staging individual hunks, partial file changes, or splitting a file's
  changes across multiple commits
---

# git-hunks

Non-interactive hunk staging for automated workflows. Replaces `git add -p` when terminal
interaction is unavailable.

## Commands

```sh
git hunks list                    # Show unstaged hunks with stable IDs
git hunks list --staged           # Show staged hunks
git hunks add '<id>' ['<id>'...]  # Stage specific hunks by ID
```

## Hunk ID Format

IDs use the pattern `file:@-old,len+new,len`, derived from diff `@@` headers. IDs remain stable as
other hunks are staged (unlike line-based approaches).

## Workflow

1. `git hunks list` to see all unstaged hunks
2. Identify which hunks belong to the current logical change
3. `git hunks add 'file:@-10,5+10,7'` to stage specific hunks
4. `git status -sb` to verify staging
5. Proceed with commit

## Shell Quoting

MUST quote hunk IDs to prevent glob expansion of `@` and `+` characters. Single quotes are safest:
`git hunks add 'path/to/file:@-10,5+10,7'`.
