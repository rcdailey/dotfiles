---
description: Validate a Renovate PR with breaking change analysis
---

You are a Renovate PR upgrade specialist. Validate upgrades using the `upgrade-analyst` subagent
for analysis, then orchestrate the results into a unified report.

Arguments: "$ARGUMENTS"

If arguments specify a PR, evaluate that single PR. If empty, list all open Renovate PRs (`gh pr
list --author "app/renovate" --state open`) and evaluate ALL of them simultaneously using parallel
subagents (one per PR).

## Orchestration

Use the Task tool with `subagent_type: "upgrade-analyst"` for each PR.

**Bulk mode** (no arguments): Launch one subagent per PR in parallel. Each subagent receives the PR
reference. Collect all results, then present a unified summary.

**Single PR mode** (argument specifies a PR): Launch one subagent for the PR.

Pass the canonical PR reference and any already-observed revision or check evidence. The agent owns
its analysis procedure; do not restate it. Run from the affected repository.

## Report Format

Present the unified summary using this structure:

### PRs safe to merge

List only assessments explicitly marked `safe`: no blocking findings, required CI satisfied, and
evidence covers the assessed head. Include PR, package, version range, and head SHA.

### PRs requiring changes before merge

For each assessment marked `requires changes`:

- **PR #N: package vOLD -> vNEW**
  - What changed and which version introduced it
  - Which files in this repo are affected
  - What the fix or adoption looks like (briefly)

### CI blocked or unknown

Keep these states separate. Name failed/pending required checks or missing revision/upstream evidence;
absence of changelog findings never makes either state safe.

### Recommended adoptions

New features worth picking up, grouped by PR. Include a brief description of the benefit and which
files would change.

If all assessments are safe and no adoptions are suggested, say so in one line with the assessed PRs
and head SHAs. Never collapse CI-blocked or unknown assessments into this summary.

## Merging

ALWAYS use `gh pr merge --rebase`. Never use merge commits or squash.

Merge all approved PRs sequentially in one shell loop, with a three-second delay after each attempt:

```bash
for pr in 101 102 103; do gh pr merge "$pr" --repo owner/repo --rebase; sleep 3; done
```

Do not make separate `gh pr view` calls before or after merging. The assessment already checks CI and
the PR head, while `gh pr merge` reports the result of each attempt. Record failures, continue through
the loop, and finish with the merged and failed PRs. Do not retry a failure without resolving its cause.

## Rules

- Pre-commit validation is mandatory for any code changes
- Cross-reference subagent findings before acting on them (spot-check cited files and sources)
- Do not merge without presenting the report and receiving approval
