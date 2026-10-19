---
name: git-conflicts
description: >-
  Use when resolving git merge or rebase conflicts, especially modify/delete (UD/DU) conflicts
  where one side deleted a file the other side changed.
---

# Git Conflicts

For UD/DU conflicts, MUST NOT blindly accept the deletion:

1. Run `git diff REBASE_HEAD...HEAD -- <file>` to see the upstream modifications being discarded.
2. Port any meaningful changes to the replacement files.
3. Resolve with `git rm <file>`.
