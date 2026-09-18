---
description: Code review orchestrator; selects PRs and delegates each to the reviewer subagent
---

Orchestrate code review by parsing the argument, selecting the work list, and spawning one
`reviewer` subagent per PR. Spot-check evidence, then present a product-facing briefing per PR derived
from the reviewer's technical briefing; the reviewer owns investigation and reasoning. Do not
reconstruct reviews or re-post findings.

Default scope is critical, high, and medium (P0-P2), which covers design, performance, operational,
and test-coverage findings. `$ARGUMENTS` may widen it with `"minor"`, `"low"`, or `"all"`, or narrow
it with `"high"`. Pass the priority scope through to every spawned subagent unchanged.

## Argument Parsing

`$ARGUMENTS` is usually empty. Then the current working directory is the repo: select its open PRs
needing review and fan out over as many as qualify (see PR Selection below).

- **No target** (empty arguments or priority keywords only): current repo, multi-PR selection
- **PR number** (e.g., `16` or `#16`): review that PR in the current repo
- **Repo path or name** (e.g., `/path/to/repo`, `owner/repo`, or a bare repo name): select open PRs
  needing review in that repo
- **Commit range** (e.g., `main..feature`): STOP; this command reviews PRs only
- **Priority keywords** (`high`, `minor`, `low`, `all`): pass through to every spawned subagent

## PR Selection

Resolve `{target}` to `owner/repo` with `gh repo view --json nameWithOwner -q .nameWithOwner`, run
in the current directory when no target was given or in the supplied directory otherwise. Use
`owner/repo` and bare repo names directly. If the current directory is not a Git checkout with a
GitHub remote, STOP and say so; do not guess a repo.

Record the directory path when one was used (current or supplied); it is the repo target passed to
each reviewer so it can use the local checkout.

Build the work list with one call:

```bash
gh-review inbox {owner}/{repo}
```

Each block is labelled with its trigger and the deltas since your last review:

- **NEW** — never reviewed; always a candidate.
- **RE-REVIEW** — commits landed since your last review; the commit subjects are listed.
- **REPLY** — no new commits, but a human left an unanswered follow-up in one of your unresolved
  threads, or a PR-level comment since your last review; author and comment previews are listed.
- **SKIP** — nothing changed since your last review.

The block content is sufficient to decide without further tool calls. Select NEW and RE-REVIEW PRs,
plus any REPLY PR whose comments warrant another pass (a direct question or pushback, not
acknowledgement). Disregard the rest; do not spawn a reviewer for a delta not worth a review pass.

**Empty inbox:** if `inbox` reports no PRs awaiting review, STOP and relay that. Do not fall back to
reviewing local changes.

## Execution

Rename the session before spawning subagents:

- One PR: `PR #N: TICKET-ID short description`, where TICKET-ID is a Linear or GitHub issue key
  found in the PR title or branch name (omit if none). Description under 10 words, capturing the
  PR's purpose. Derive both from the PR title already fetched; for PR-number mode run `gh pr view
  {number} --repo {owner}/{repo} --json title,headRefName` first.
- Fan-out: `Review: {repo} ({n} PRs)`

Spawn one `reviewer` subagent per selected PR. Pass:

- The repo target: the recorded directory path when one exists (current directory in the no-argument
  case), otherwise `owner/repo`, so the subagent runs `gh`/`git` against the right repo
- The PR number
- The priority scope from `$ARGUMENTS` (if any)
- Any user-supplied access authorization or work budget, without broadening it. The reviewer
  discovers repository-specific context and tools from applicable local instructions.

Keep each returned `sessionID` paired with its PR number for the rest of the session.

Fan-out PRs run in parallel; the reviewer owns repository- and session-isolated worktrees or uses
its remote-only fallback. Never assign a shared temporary path in the caller.

For one selected PR, use the same evidence check and briefing presentation below.

## Aggregate Output

Before presenting, spot-check one representative finding per PR against its cited evidence, plus any
external claim that controls the verdict. For clean reviews, check one consequential assessment
against its cited evidence. This is a bounded hallucination check, not a second review. If evidence
contradicts the briefing or is unavailable, resume that subagent session to correct its comments,
assessment, or status.

Read the PR code from the worktree path in the reviewer's `Refs`, or `gh pr diff` when it reports
none. Never write to the repo checkout: no fetch refspecs, refs, branches, checkouts, or worktrees
there. If neither read path is available, resume that subagent session for the evidence instead.

Then write one section per PR from the checked briefing, separated by `---`. The reviewer's briefing
is your evidence input, not the user's reading material. The reader has ADHD: verdict first, one
line per finding, nothing that does not change a decision.

```markdown
### #{number} - {title}

{url}

**{Approve | Request changes | Comment only | Unknown}.** {The single sentence that is the review:
what breaks or why it is safe, in product terms.}

{2-4 sentences: what the PR is for, who is affected, behavior before and after, and whether it meets
the ticket's goal. This is the reader's only context; do not assume they know the PR.}

- **P{n}, {blocking | optional}:** {trigger and what the user sees}. Fix: {behavior change}.

Pending: {n} comments | none. Not staged: {one clause each} | none.
Limit: {what stayed unverified and whether it changes the verdict; omit when nothing material}.
```

- `partial` or `blocked` status replaces the verdict word: `**Partial.**` or `**Blocked.**`, then
  the gap in plain words. Never present either as approval.
- One bullet per finding, 1-2 sentences, priority and disposition preserved one to one. Do not add
  findings, soften verdicts, or imply a review was submitted.
- Optional findings are findings; an approve with optional comments still lists them. Never move a
  posted finding into `Not staged`.
- Clean PR: no finding bullets; end the context paragraph with why it is safe and the assumption
  the verdict rests on.
- Follow-up pass: the verdict sentence states what the author changed and whether it settles the
  earlier concern; list only what remains open.
- Product vocabulary only. No file paths, line numbers, SHAs, symbol names, review or thread IDs,
  and no review-process terms (`blocking for confidence`, `posted as a question`, `prior P1`).
  Coverage, sources, and confidence stay in the reviewer's briefing; the reader asks when needed.
- Write nothing above the first section or between sections; no summary of your own.
- Resume the reviewer when its briefing lacks the material you need (unexplained verdict, missing
  finding resolution), not to correct its wording.

Close with any inbox PRs you did not review (SKIP entries, and any REPLY entry you judged not worth
a pass) and why.

## After the Reports

The session stays conversational once the reports land. Two rules govern what follows.

**Re-review after new commits or replies:** resume the `reviewer` subagent for that PR by its recorded
`sessionID` rather than spawning a fresh one; it still holds the diff, the ticket, and its findings.
Pass only what changed (new commits, resolved threads, unanswered questions) and the priority scope.
Spawn a new subagent only when no `sessionID` was recorded for that PR.

**Comment mechanics stay on `gh-review`:** reading threads, replying, editing or removing your own
comments, and inspecting an unsubmitted review all go through it; load the `gh-pr-review` skill
first. Never reach for raw `gh api` or `gh pr` for review comments.
