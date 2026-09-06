---
description: Code review orchestrator; selects PRs and delegates each to the reviewer subagent
---

Orchestrate code review by parsing the argument, selecting the work list, and spawning one
`reviewer` task per PR. Spot-check evidence, then present a private comprehension briefing per PR;
the reviewer owns investigation and reasoning. Do not reconstruct reviews or re-post findings.

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

The block content is sufficient to decide without further tool calls. Select NEW and RE-REVIEW PRs,
plus any REPLY PR whose comments warrant another pass (a direct question or pushback, not
acknowledgement). Disregard the rest; do not spawn a reviewer for a delta not worth a review pass.

**Empty inbox:** if `inbox` reports no PRs awaiting review, STOP and relay that. Do not fall back to
reviewing local changes.

## Execution

Rename the session before spawning tasks:

- One PR: `PR #N: TICKET-ID short description`, where TICKET-ID is a Linear or GitHub issue key
  found in the PR title or branch name (omit if none). Description under 10 words, capturing the
  PR's purpose. Derive both from the PR title already fetched; for PR-number mode run `gh pr view
  {number} --repo {owner}/{repo} --json title,headRefName` first.
- Fan-out: `Review: {repo} ({n} PRs)`

Spawn one `reviewer` task per selected PR. Pass:

- The repo target (directory path or `owner/repo`) so the subagent runs `gh`/`git` against the right
  repo
- The PR number
- The priority scope from `$ARGUMENTS` (if any)
- Any user-supplied access authorization or work budget, without broadening it. The reviewer
  discovers repository-specific context and tools from applicable local instructions.

Keep each returned task id paired with its PR number for the rest of the session.

Fan-out PRs run in parallel; the reviewer owns repository- and session-isolated worktrees or uses
its remote-only fallback. Never assign a shared temporary path in the caller.

For one selected PR, use the same evidence check and briefing presentation below.

## Aggregate Output

Preserve `partial` and `blocked` statuses; do not present either as approval. Before relaying,
spot-check one representative finding per PR against its cited evidence, plus any external claim
that controls the verdict. For clean reviews, check one consequential assessment against its cited
evidence. This is a bounded hallucination check, not a second review. If evidence contradicts the
briefing or is unavailable, resume that task to correct its comments, assessment, or status.

For multiple PRs, lead with one linked overview bullet per PR: status, proposed verdict, pending
comment count, and any decision or missing evidence requiring user attention. Derive these only from
the checked briefings; do not invent readiness or imply a review was submitted.

Then relay each reviewer's briefing verbatim, separated by `---`. Every PR must answer all three
questions, including clean, partial, blocked, and follow-up outcomes. If a briefing omits answers,
causal explanation, or evidence limits, resume the reviewer to correct it. Do not impose a line cap
that removes comprehension; reject repeated summaries and investigation diaries instead.

Close with any inbox PRs you did not review (SKIP entries, and any REPLY entry you judged not worth
a pass) and why.

## After the Reports

The session stays conversational once the reports land. Two rules govern what follows.

**Re-review after new commits or replies:** resume the `reviewer` task for that PR by its recorded
task id rather than spawning a fresh one; it still holds the diff, the ticket, and its own findings.
Pass only what changed (new commits, resolved threads, unanswered questions) and the priority scope.
Spawn a new task only when no id was recorded for that PR.

**Comment mechanics stay on `gh-review`:** reading threads, replying, editing or removing your own
comments, and inspecting an unsubmitted review all go through it; load the `gh-pr-review` skill
first. Never reach for raw `gh api` or `gh pr` for review comments.
