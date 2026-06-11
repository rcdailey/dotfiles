---
description: Address PR review comments (triage, fix, push, reply to each comment)
---

Address review comments on pull request $ARGUMENTS. Argument format: PR number (e.g., `42`) or
`owner/repo PR-number` when running outside the PR's worktree.

## Step 1: Resolve the PR

Parse $ARGUMENTS:

- Bare number or `#N`: run `gh pr view N --json number,headRefName,baseRefName,url,title` from the
  current directory to get repo context.
- `owner/repo N`: run `gh pr view N --repo owner/repo --json
  number,headRefName,baseRefName,url,title`.

Capture: PR number, head ref, base ref, PR URL, repo (in `owner/repo` form via `gh repo view --json
nameWithOwner -q .nameWithOwner`).

## Step 2: Orient to the diff (fresh session only)

If this is a fresh session without prior context on these changes, read the diff before triaging
comments:

```bash
git fetch origin <headRef>
git diff origin/<baseRef>...origin/<headRef>
```

This provides the change context needed to evaluate comment validity.

## Step 3: Read unresolved comments

```bash
gh-review view <owner/repo> <number>
```

This returns all unresolved review threads and conversation comments. If there are no unresolved
comments, print "No unresolved comments." and stop.

## Step 4: Triage

For each comment, decide one of:

- **Fix**: the comment identifies a genuine issue; implement the fix.
- **Disagree**: the suggested change is incorrect, unnecessary, or conflicts with project
  conventions; reply explaining why, then leave the code as-is.
- **Nitpick accepted**: style or formatting feedback that is valid; implement it.
- **Bot noise**: automated comment that adds no signal (duplicate, off-topic, outdated lint); skip
  silently.

Triage criteria:

- Evaluate correctness against the codebase and the language/framework behavior, not just the
  comment's phrasing.
- Do not apply a change simply because a reviewer requested it; apply it because it is correct.
- Disagreements MUST get an explicit reply; silent skips are not allowed.

## Step 5: Implement fixes

Apply all accepted fixes. Run the project's full check suite and confirm it is green before pushing.
If checks fail, fix them before proceeding.

## Step 6: Push

```bash
git push
```

## Step 7: Reply to comments

For each comment that was addressed (fixed, disagreed, or nitpick accepted), reply via:

```bash
gh-review reply <owner/repo> <number> <comment-node-id> --body "<reply>"
```

Reply bodies:

- Fixed: one sentence describing what was changed (e.g., "Fixed: extracted the method as
  suggested.")
- Disagreed: clear explanation of why the change was not applied; reference specific code or docs if
  relevant.
- Nitpick accepted: brief acknowledgement (e.g., "Done.")
- Bot noise: no reply.

## Rules

- MUST evaluate each comment on its merits; never silently skip a human comment.
- MUST run the full check suite green before pushing.
- MUST reply to every non-noise comment, including disagreements.
- MUST NOT merge the PR; the human merges after reviewing replies.
- MUST NOT use TodoWrite or task tracking.
- Do not create or modify files outside the worktree.
