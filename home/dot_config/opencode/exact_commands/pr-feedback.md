---
description: Address PR feedback (failing CI checks and review comments; triage, fix, push, reply)
agent: dispatch
---

Address feedback on pull request $ARGUMENTS: failing CI checks and unresolved review comments.
Argument format: PR number (e.g., `42`) or `owner/repo PR-number` when running outside the PR's
worktree.

## Step 1: Resolve the PR

Parse $ARGUMENTS:

- Bare number or `#N`: run `gh pr view N --json number,headRefName,baseRefName,url,title,body` from
  the current directory to get repo context.
- `owner/repo N`: run `gh pr view N --repo owner/repo --json
  number,headRefName,baseRefName,url,title,body`.

Capture: PR number, head ref, base ref, PR URL, repo (in `owner/repo` form via `gh repo view --json
nameWithOwner -q .nameWithOwner`).

## Step 2: Orient

This command runs in a fresh session; the PR carries the context. Read, in order:

1. The PR body, especially its `## Design notes` section (constraints, rejected alternatives, dead
   ends from the original implementation). Weigh these when triaging; a reviewer suggestion may
   already be a rejected alternative.
2. The diff:

```bash
git fetch origin <headRef>
git diff origin/<baseRef>...origin/<headRef>
```

Threads from earlier iterations (step 4 output) include prior replies recording past decisions; do
not relitigate a decision already explained unless the reviewer has added a new argument.

## Step 3: Check CI status

```bash
gh pr checks <number> --repo <owner/repo> --json name,state,bucket,link
```

For each check in the `fail` bucket, extract the run ID from `link` and fetch only the failing
output:

```bash
gh run view <run-id> --repo <owner/repo> --log-failed
```

Logs can be long; extract the failing test names, assertion output, or error messages rather than
keeping the full log. Triage each failure:

- **Caused by this PR**: reproduce locally if possible, fix it.
- **Flaky or infrastructure** (network timeout, runner error, failure clearly unrelated to the
  diff): rerun once with `gh run rerun <run-id> --repo <owner/repo> --failed`. If it fails again for
  the same unrelated reason, leave a PR comment describing the failure and why it is not addressable
  from this PR; do not churn on it.

## Step 4: Read unresolved comments

```bash
gh-review view <owner/repo> <number>
```

This returns all unresolved review threads and conversation comments. If there are no unresolved
comments and no failing checks, print "Nothing to address." and stop.

## Step 5: Triage comments

For each comment, decide one of:

- **Fix**: the comment identifies a genuine issue; implement the fix.
- **Disagree**: the suggested change is incorrect, unnecessary, or conflicts with project
  conventions; reply explaining why, then leave the code as-is.
- **Nitpick accepted**: style or formatting feedback that is valid; implement it.
- **Not applicable**: automated comment that adds no signal (duplicate, off-topic, outdated lint);
  no code change, but still gets a one-line factual reply stating why.

GitHub code scanning findings arrive as review threads from `github-advanced-security[bot]`; triage
them like any other bot comment (fix genuine findings, explain false positives in the reply).

Triage criteria:

- Evaluate correctness against the codebase and the language/framework behavior, not just the
  comment's phrasing.
- Do not apply a change simply because a reviewer requested it; apply it because it is correct.
- Every comment gets a reply, human or bot; silent skips are not allowed.

## Step 6: Implement fixes

Apply all accepted fixes (CI failures and comments). Run the project's full check suite and confirm
it is green before pushing. If checks fail, fix them before proceeding.

## Step 7: Push

If any commits were made:

```bash
git push
```

## Step 8: Reply to comments

For every triaged comment (fixed, disagreed, nitpick accepted, or not applicable), reply via:

```bash
gh-review reply <owner/repo> <number> <comment-node-id> --body "<reply>"
```

Reply bodies:

- Fixed: one sentence describing what was changed (e.g., "Fixed: extracted the method as
  suggested.")
- Disagreed: clear explanation of why the change was not applied; reference specific code or docs if
  relevant.
- Nitpick accepted: brief acknowledgement (e.g., "Done.")
- Not applicable: one-line factual reason (e.g., "Not applicable: duplicate of the thread on
  src/foo.ts.").

Bot authors (`[bot]` suffix, CodeRabbit, github-advanced-security, CI tools): neutral, factual
statements describing what was done and why, or why nothing will be done. Never address the bot
conversationally. Review bots learn from replies, so every bot comment gets one, and it is
conclusive: state the decision once, do not invite follow-up.

## Rules

- MUST evaluate each comment on its merits; never silently skip any comment, human or bot.
- MUST NOT rerun a flaky check more than once; after that, comment on the PR and move on.
- MUST run the full check suite green before pushing.
- MUST reply to every comment, including disagreements; replies to bots are conclusive.
- MUST NOT merge the PR; the human merges after reviewing replies.
- MUST NOT use TodoWrite or task tracking.
- Do not create or modify files outside the worktree.
