---
description: Sync the humanizer skill with upstream blader/humanizer
---

Sync `home/dot_config/opencode/exact_skills/humanizer/SKILL.md` with the upstream repository
[blader/humanizer](https://github.com/blader/humanizer).

## Process

### 1. Check for upstream changes

Use `git log` on the local SKILL.md to find the last sync point (look for commits mentioning "sync",
"upstream", "humanizer", or the initial commit that added the file).

Use `gh api` to list commits on `blader/humanizer` for `SKILL.md` since that date. If nothing
changed, stop and tell the user the skill is up to date.

### 2. Confirm with user

Show a summary of upstream changes and ask whether to proceed.

### 3. Save current frontmatter

Read the current local SKILL.md and capture the YAML frontmatter block (everything between the
opening `---` and closing `---`, inclusive). You will need this in step 5.

### 4. Overwrite with upstream

Download via bash:

```sh
gh api repos/blader/humanizer/contents/SKILL.md --jq '.content' | base64 -d > \
  home/dot_config/opencode/exact_skills/humanizer/SKILL.md
```

### 5. Apply post-sync edits

Delegate to a `general` subagent. Pass it:

- The file path
- The exact frontmatter captured in step 3 (to replace upstream's frontmatter)
- Instruction to remove the "Voice Calibration (Optional)" section entirely (it is redundant with
  Communication Voice in the global AGENTS.md)
- Instruction to use the Edit tool for all changes

### 6. Review

Read the file yourself and verify:

- Frontmatter matches the pre-sync version exactly
- Voice Calibration section is removed
- No double blank lines or formatting artifacts
- Content flows from "Your Task" directly into "PERSONALITY AND SOUL"

If issues remain, delegate corrections to the subagent again.

### 7. Report

Tell the user what was synced: new patterns, modified patterns, and any structural changes.

## Rules

- MUST use `gh api` to fetch the upstream file (not webfetch or git clone)
- MUST preserve the local frontmatter exactly as it was before the sync
- MUST remove the Voice Calibration section after overwriting
- MUST delegate mechanical edits to a `general` subagent; review the result yourself
- MUST NOT commit changes; leave that to the user
