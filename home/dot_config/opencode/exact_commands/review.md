---
description: Code review orchestrator; selects PRs and delegates each to the reviewer subagent
---

Orchestrate code review by parsing the argument, selecting the work list, and spawning one
`reviewer` task per PR. Relay each subagent's report; do not re-verify or re-post findings.

Focus is critical/high priority issues unless `$ARGUMENTS` includes `"medium"`, `"minor"`, `"low"`,
or `"all"`. Pass the priority scope through to every spawned task unchanged.

## Argument Parsing

- **PR number** (e.g., `16` or `#16`): review that PR in the current repo
- **Repo path or name** (e.g., `/path/to/repo`, `owner/repo`, or a bare repo name): select open PRs
  needing review (see PR Selection below)
- **Commit range** (e.g., `main..feature`): delegate to `reviewer` in commit-range mode
- **No arguments**: delegate to `reviewer` in local-changes mode
- **Priority keywords** (`medium`, `minor`, `low`, `all`): pass through to every spawned task

## PR Selection (repo path or name only)

Resolve the repo target for `gh`:

- Directory path: derive with `gh repo view --json nameWithOwner -q .nameWithOwner` executed in that
  directory, or pass via `workdir`
- `owner/repo` or bare repo name: pass directly as `--repo {target}`

Build the work list as the union of two queries:

**1. Never reviewed** — PRs the user has not yet reviewed:

```bash
gh pr list --repo {target} --state open \
  --search "-author:@me -reviewed-by:@me -is:draft" \
  --json number,title,url,author,updatedAt
```

**2. Re-review** — PRs the user reviewed but new commits arrived since:

```bash
gh pr list --repo {target} --state open \
  --search "-author:@me reviewed-by:@me -is:draft" \
  --json number,title,url,author,updatedAt
```

For each PR in the re-review list, fetch the user's latest review timestamp and the head commit
date, then include it only when commits were pushed after the last review:

```bash
gh pr view {number} --json latestReviews,commits \
  --jq '{reviews: .latestReviews, lastCommit: (.commits | last)}'
```

If a PR in the re-review list has no new commits since the last review, skip it and note it in the
aggregate output.

**Empty work list:** STOP and report: no open PRs are awaiting review in `{target}`. Do not fall
back to reviewing local changes.

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

Fan-out PRs run in parallel; each gets its own `/tmp/pr-review-{n}` worktree so parallel execution
is safe.

For single-PR, commit-range, and local-changes modes, spawn one task and relay its report directly.

## Aggregate Output

Relay each subagent's report verbatim, preserving every field of its return template (PR URL,
verdict, pending review ID and comment count, the four finding buckets, citations, confidence).
MUST NOT summarize, truncate, reorder, or drop fields; the report is the deliverable. Separate
multiple PRs with `---`.

For fan-out, prefix the reports with a one-line-per-PR index (`#N {verdict} - {n} comments -
{url}`), then the full reports.

Close with any PRs skipped from the re-review list and why, and the reminder that pending reviews
are unsubmitted. Do not add analysis or re-post comments.
