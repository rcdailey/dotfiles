---
description: Sync the humanizer skill with upstream blader/humanizer
---

Sync `home/dot_config/opencode/exact_skills/humanizer/SKILL.md` with the upstream repository
[blader/humanizer](https://github.com/blader/humanizer).

The local skill is a semantic compression of upstream, not a summary. Effectiveness takes priority
over size. Upstream owns pattern detection; local sections own OpenCode delivery and user voice.

## Process

### 1. Check for upstream changes

Use `git log` on the local SKILL.md to find the last sync point (look for commits mentioning "sync",
"upstream", "humanizer", or the initial commit that added the file).

Use `gh api` to list commits on `blader/humanizer` for `SKILL.md` since that date. Inspect linked
issues and PRs when commit messages do not explain the behavioral reason. If nothing changed, stop
and tell the user the skill is up to date.

### 2. Confirm with user

Show a summary of upstream changes and ask whether to proceed.

### 3. Identify ownership

Read the local skill. Capture these local-owned sections exactly:

- YAML frontmatter
- `Choose the mode`
- `Core rules`
- `Internal process`
- `Compact example`
- The complete `BEGIN LOCAL ADDITION` through `END LOCAL ADDITION` block

Treat the numbered pattern catalog and detection guidance as upstream-owned behavior.

### 4. Fetch upstream

Verify `/tmp/opencode` exists, then download the upstream skill:

```sh
gh api repos/blader/humanizer/contents/SKILL.md --jq '.content' | base64 -d > \
  /tmp/opencode/humanizer-upstream.md
```

Do not overwrite the local skill with this file.

### 5. Merge behavior

Read the downloaded upstream skill, then delegate to a `general` subagent. Pass it:

- The local and downloaded file paths
- The local-owned sections captured in step 3
- The merge contract below
- Instruction to edit the local file surgically, never rewrite it wholesale

Merge contract:

- Preserve every upstream numbered pattern as an individual local section. Never group patterns.
- Preserve each pattern's detection behavior: name, watch terms or rule, problem, exceptions, and
  one compact before/after example.
- Preserve upstream safeguards for source fidelity, false positives, information retention, and
  human writing signals.
- Import new patterns and semantic fixes. Keep upstream numbering unless upstream renumbers it.
- Compact only duplicated wording, scaffolding, theory, or oversized examples. Shorten an example
  only when it still demonstrates the same distinction and does not invent facts.
- Preserve local-owned sections exactly. Integrate upstream safety fixes into upstream-owned
  sections or report a conflict for primary review.
- Do not import upstream frontmatter, voice calibration, invocation modes, process/output ceremony,
  or duplicated showcase examples.
- Keep the upstream reference attribution once.
- When uncertain whether wording carries detection behavior, retain it.

### 6. Review

Read the file yourself and verify:

- Frontmatter and the complete local-addition block match their pre-sync versions exactly
- Every upstream numbered pattern exists as an individual local section in the same order
- Every pattern has its problem and a compact example; applicable watch terms and exceptions remain
- Upstream source-fidelity, false-positive, and human-writing safeguards remain
- No upstream voice calibration, invocation modes, output ceremony, or showcase duplication leaked
  into local-owned sections
- No double blank lines or formatting artifacts

Run the repository checks that apply to the changed Markdown file. If issues remain, delegate
mechanical corrections to the same subagent and review again.

### 7. Report

Tell the user what was synced: new or modified patterns, safeguards, examples, and structural
changes. Call out upstream content intentionally omitted as duplication or runtime ceremony.

## Rules

- MUST use `gh api` to fetch the upstream file (not webfetch or git clone)
- MUST preserve all local-owned sections, especially the marked user voice block
- MUST preserve upstream detection behavior; effectiveness outranks token reduction
- MUST NOT collapse numbered patterns into categories or remove their calibration examples
- MUST delegate mechanical edits to a `general` subagent; review the result yourself
- MUST NOT commit changes; leave that to the user
