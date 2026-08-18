Orchestrate code review by parsing the argument, selecting the work list, and spawning one
`reviewer` task per PR. Spot-check the returned evidence, then relay the corrected subagent report;
do not reproduce the full review or re-post findings.

Focus is critical/high priority issues unless `$ARGUMENTS` includes `"medium"`, `"minor"`, `"low"`,
or `"all"`. Pass the priority scope through to every spawned task unchanged.

## Argument Parsing

- **PR number** (e.g., `16` or `#16`): review that PR in the current repo
- **Repo path or name** (e.g., `/path/to/repo`, `owner/repo`, or a bare repo name): select open PRs
  needing review (see PR Selection below)
- **No target** (empty arguments or priority keywords only): select open PRs in the current repo
- **Commit range** (e.g., `main..feature`): STOP; this command reviews PRs only
- **Priority keywords** (`medium`, `minor`, `low`, `all`): pass through to every spawned task

## PR Selection

Resolve `{target}` to `owner/repo`:

- Directory path: run `gh repo view --json nameWithOwner -q .nameWithOwner` in that directory
- `owner/repo` or bare repo name: use directly
- No target: derive the current repo with `gh repo view --json nameWithOwner -q .nameWithOwner`

Build the work list with one call:

```bash
gh-review inbox {target}
```

Each block is labelled with its trigger and the deltas since your last review:

- **NEW** — never reviewed; always a candidate.
- **RE-REVIEW** — commits landed since your last review; the commit subjects are listed.
- **REPLY** — no new commits, but a human left a follow-up in one of your threads or a PR-level
  comment since your last review; author and comment previews are listed.
- **SKIP** — nothing changed since your last review.

The block content is sufficient to decide without further tool calls. Select NEW and RE-REVIEW
PRs, plus any REPLY PR whose comments warrant another pass (a direct question or pushback, not
acknowledgement). Disregard the rest; do not spawn a reviewer for a delta not worth a review pass.

**Empty inbox:** if `inbox` reports no PRs awaiting review, STOP and relay that. Do not fall back
to reviewing local changes.

## Execution

Rename the session before spawning tasks:

- One PR: `PR #N: TICKET-ID short description`, where TICKET-ID is a Linear or GitHub issue key
  found in the PR title or branch name (omit if none). Description under 10 words, capturing the
  PR's purpose. Derive both from the PR title already fetched; for PR-number mode run `gh pr view
  {number} --json title,headRefName` first.
- Fan-out: `Review: {repo} ({n} PRs)`

Spawn one `reviewer` task per selected PR. Pass:

- The repo target (directory path or `owner/repo`) so the subagent runs `gh`/`git` against the right
  repo
- The PR number
- The priority scope from `$ARGUMENTS` (if any)

Keep each returned task id paired with its PR number for the rest of the session.

Fan-out PRs run in parallel; each gets its own `/tmp/pr-review-{n}` worktree so parallel execution
is safe.

For one selected PR, spawn one task and relay its report directly.

## Aggregate Output

Before relaying, spot-check one representative reported finding per PR against its cited path and
line, plus any external claim that controls the verdict. This is a bounded hallucination check, not
a second review. If the evidence contradicts the report, resume that PR's reviewer task with the
discrepancy and require it to correct its pending comments and report.

Relay each subagent's report verbatim, preserving every field of its return template. MUST NOT
summarize, expand, reorder, or drop fields; the report is already compressed to an index and the
pending review carries the detail. Separate multiple PRs with `---`. Add no index, preamble, or
analysis of your own.

If a report exceeds its 20-line budget or pads findings with prose, resume the reviewer task and
require a compliant report rather than editing it in the caller context.

Close with any inbox PRs you did not review (SKIP entries, and any REPLY entry you judged not
worth a pass) and why.

## After the Reports

The session stays conversational once the reports land. Two rules govern what follows.

**Re-review after new commits or replies:** resume the `reviewer` task for that PR by its recorded
task id rather than spawning a fresh one; it still holds the diff, the ticket, and its own findings.
Pass only what changed (new commits, resolved threads, unanswered questions) and the priority scope.
Spawn a new task only when no id was recorded for that PR.

**Comment mechanics stay on `gh-review`:** reading threads, replying, editing or removing your own
comments, and inspecting an unsubmitted review all go through it; load the `gh-pr-review` skill
first. Never reach for raw `gh api` or `gh pr` for review comments.
