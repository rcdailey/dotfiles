---
description: Code review orchestrator; selects PRs and delegates each to the reviewer subagent
---

Orchestrate code review by parsing the argument, selecting the work list, and spawning one
`reviewer` task per PR. Spot-check evidence, then present a product-facing briefing per PR derived
from the reviewer's technical briefing; the reviewer owns investigation and reasoning. Do not
reconstruct reviews or re-post findings.

Default scope is critical, high, and medium (P0-P2), which covers design, performance, operational,
and test-coverage findings. `$ARGUMENTS` may widen it with `"minor"`, `"low"`, or `"all"`, or narrow
it with `"high"`. Pass the priority scope through to every spawned task unchanged.

## Argument Parsing

- **PR number** (e.g., `16` or `#16`): review that PR in the current repo
- **Repo path or name** (e.g., `/path/to/repo`, `owner/repo`, or a bare repo name): select open PRs
  needing review (see PR Selection below)
- **No target** (empty arguments or priority keywords only): select open PRs in the current repo
- **Commit range** (e.g., `main..feature`): STOP; this command reviews PRs only
- **Priority keywords** (`high`, `minor`, `low`, `all`): pass through to every spawned task

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

Preserve `partial` and `blocked` statuses; do not present either as approval. Before presenting,
spot-check one representative finding per PR against its cited evidence, plus any external claim
that controls the verdict. For clean reviews, check one consequential assessment against its cited
evidence. This is a bounded hallucination check, not a second review. If evidence contradicts the
briefing or is unavailable, resume that task to correct its comments, assessment, or status.

Then write one section per PR from the checked briefing, separated by `---`. The reviewer's briefing
is your evidence input, not the user's reading material: translate it into product terms.

```markdown
### [#{number} - {title}]({url})

**Status:** {complete | partial | blocked} - {gap in plain words, if any}
**Verdict:** {approve | request changes | comment-only | unknown} - {one plain sentence}
**Review:** {n} pending comments (unsubmitted) | none

### What is changing, and what is my assessment?

{2-4 sentences: who is affected, before vs after, ticket goal met or not, why the verdict}

### When does the concern matter, and what happens?

- **P{n}, {blocking | optional}:** {user or system scenario that triggers it; what they experience}

### What would resolve the concern or change my assessment?

- {what must change, in behavior terms; why it blocks or why it can wait}

**Not staged:** {below-scope items, one plain sentence each, or none}
**Coverage:**

- Inspected: {behaviors traced, one sentence}
- Checks: {what ran or what CI proves, one sentence}
- Limits: {what stayed unverified and whether it changes the verdict, one sentence}

**Sources:** {external docs, Context7 IDs, URLs, tickets, live systems; or none}
**Finding confidence:** {high | medium | low | n/a} - {short active sentences}
```

- Preserve status, verdict, priority, disposition, and every finding one to one; translate mechanism
  into user-visible behavior. Do not add findings, soften verdicts, or imply a review was submitted.
- Optional findings are findings: an approve verdict with optional comments still uses the three
  question headings. Never move a posted finding into `Not staged`.
- Clean PR (no findings, no open concern): replace the three question headings with one
  `### Assessment` paragraph of 3-5 sentences covering what changes for users, why it is safe, and
  the assumption the verdict rests on. Keep the remaining fields.
- No file paths, line numbers, SHAs, symbol names, SQL, decorators, or review and thread IDs
  anywhere in the section. Those stay in the reviewer's briefing for evidence checks and follow-ups.
- Answer 1 is 2-4 sentences; answers 2 and 3 are one bullet per finding of 2-3 sentences each;
  coverage bullets are one sentence each. Expand only for a distinct consequence.
- Write nothing above the first section or between sections; no summary of your own.
- `Finding confidence` uses short active sentences, one idea each, without jargon.
- Resume the reviewer when its briefing lacks the material you need to write a section (missing
  answers, unexplained verdict, missing coverage), not to correct its wording.

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
