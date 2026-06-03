---
description: Code review for PRs with GitHub-ready comments
---

Review code for a pull request and post findings as a pending review via `gh-review`, without
submitting it. MUST load the `gh-pr-review` skill before posting any comments.

Focus on critical/high priority issues unless $ARGUMENTS includes "medium", "minor", "low", or
"all". Bias toward fewer, higher-signal comments. A review with 2 critical findings is better than
one with 8 comments where 6 are nits.

## Argument Parsing

- PR number (e.g., `16` or `#16`): Review pull request
- Repo path or name (e.g., `/path/to/repo`, `owner/repo`, or a bare repo name): Auto-select an open
  PR the user has not reviewed (see step 0)
- Commit range (e.g., `main..feature`): Review commits
- No arguments: Review staged/unstaged changes
- Include "medium", "minor", "low", "all": Add lower priority issues section

## Process

### 0. Auto-Select a PR (repo path or name only)

When the argument is a directory path or a repo name (not a PR number, commit range, or empty), pick
an open PR the user has not reviewed instead of being handed a number.

Resolve the repo target for `gh`:

- Directory path: run subsequent `gh` commands with `--repo` resolved from that path, e.g.
  `gh repo view --json nameWithOwner -q .nameWithOwner` executed in that directory, or pass the path
  via the `workdir` of the call.
- `owner/repo` or bare repo name: pass directly as `--repo {target}` (a bare name resolves against
  the user's default owner).

List open PRs the user has neither authored nor reviewed, oldest first:

```bash
gh pr list --repo {target} --state open --search "-author:@me -reviewed-by:@me" \
  --json number,title,url,author,updatedAt
```

If the list is empty, STOP and report: no open PRs are awaiting the user's review in `{target}`. Do
not fall back to reviewing local changes.

Otherwise select the least-recently-updated PR (first entry by `updatedAt` ascending) and continue
from step 1 using its number. State which PR was auto-selected and why before
proceeding.

### 1. Gather Context

**For PRs:**

Fetch PR metadata with specific fields only:

```bash
gh pr view {number} --json title,body,labels,baseRefName,headRefName,url
```

Fetch the PR head ref and create a detached worktree. If a worktree from a previous review of the
same PR exists, remove it first:

```bash
git worktree remove --force /tmp/pr-review-{number} 2>/dev/null
git fetch origin pull/{number}/head &&
  git worktree add --detach /tmp/pr-review-{number} FETCH_HEAD
```

Get the changed file list using local git (not `gh pr diff`):

```bash
git diff --name-only FETCH_HEAD...$(git merge-base FETCH_HEAD origin/{base})
```

Note the worktree path (`/tmp/pr-review-{number}`) for file reads in the analysis step. The worktree
is left in place after the review so you can reference files while posting comments.

Do NOT install dependencies, run tests, or run build commands in the worktree. Only do so if a
specific finding later requires it (e.g., a type error you can't confirm statically).

Fetch existing comments using `gh-review view`:

```bash
gh-review view {owner}/{repo} {number}
```

This returns all unresolved review threads and conversation comments (including bot comments) in a
single query with LLM-optimized prose output. Resolved threads are filtered out by default.

**For commits:** `git log {range} --oneline` and `git diff {range}`

**For current changes:** `git status` and `git diff HEAD`

### 2. Skip Already-Flagged Issues

Before formulating feedback, cross-reference against the comment output from `gh-review view`. If a
bot or human already flagged an issue, leave it alone; don't post a second comment even if the
existing one is incomplete or could be improved. Only post comments that identify net new issues not
raised anywhere on the PR.

### 3. Analyze

Read the changed files from the worktree path (or current working copy for non-PR reviews). Read at
most 2-3 directly relevant callsites per finding to understand how the changed code is used. Do not
explore broadly or read unrelated files.

Do not read README, docs/, wiki, or other documentation unless a specific finding requires that
context.

Apply the review priorities and verification rules from the `gh-pr-review` skill.

MUST verify technical claims with `ctx7` for every library, framework, language, tool, CLI, or
standard referenced in a finding. This is not optional; unverified assertions produce hallucinated
review feedback. Run `ctx7 library <name> <query>` to resolve an ID, then `ctx7 docs <id> <query>`
for the specific behavior. Record every `ctx7` source consulted for the Citations section. Do NOT
delegate to the researcher subagent or use web search. If `ctx7` lacks coverage for a given claim,
reframe the comment as an open question rather than asserting something unverifiable, and note the
gap in Citations.

Only use local `git diff` with path filters when a specific finding needs diff hunk context for line
targeting. Do not fetch the full diff.

### 4. Compose and Post Comments

Load the `humanizer` skill before composing comment bodies (not in parallel with posting). Apply the
tone and etiquette guidelines from the `gh-pr-review` skill.

**Start or reuse a pending review:**

Check the `gh-review view` output from step 1. If it includes a `PENDING REVIEWS` section, reuse
that `PRR_...` ID. Otherwise start a new one:

```bash
gh-review start {owner}/{repo} {number}
```

**Compose each comment body as markdown:**

Write like a colleague, not a measurement report. State findings and conclusions; omit the
verification methodology that led to them. Avoid file sizes, match counts, read counts, and similar
quantifiers. Say what you found, not how many operations it took to find it.

Refer to code by names a developer already knows: class names, method names, variable names. In
comment prose, a bare name like `CaseRepository` is almost always sufficient; add a path only when
the name is ambiguous.

Do not hard-wrap prose paragraphs. Each paragraph is a single unbroken line; separate paragraphs
with blank lines. GitHub's UI wraps at render time.

Include a `suggestion` block when a concrete fix exists and the comment targets a line in the diff:

````markdown
{Explanation of the issue and why it matters. End with suggestion.}

```suggestion
{verbatim replacement for the targeted line range}
```
````

When a comment falls back to file-level (target lines outside the diff), `suggestion` blocks do not
render correctly. Use a `diff` block instead, with a `# L{start}-{end}` annotation and
space-prefixed context lines for orientation:

````markdown
{Explanation of the issue and why it matters. End with suggested change.}

```diff
# L180-183
 contextLine();
-oldCode();
+newCode();
 contextLine();
```
````

**Post each comment using `gh-review comment`:**

Single-line (targets one line, no `--start-line`):

```bash
gh-review comment --review-id PRR_... --path {file} \
  --line {N} --body '{body}'
```

Multi-line (targets a range):

```bash
gh-review comment --review-id PRR_... --path {file} \
  --start-line {start} --line {end} --body '{body}'
```

Line range rules:

- Single-line: `--line N` only. Do not pass `--start-line`.
- Multi-line: `--start-line N --line M` where N < M.
- The range defines what a `suggestion` block replaces when applied. Do not include surrounding
  context lines; they would be deleted when the suggestion is applied.
- When a single-line comment has a multi-line suggestion, use `--line N` only. The suggestion
  content replaces that one line regardless of how many lines the replacement contains.

When a line target is outside the diff, `comment` automatically retries as a file-level comment on
the same file. The output includes a `note:` field explaining the fallback. No manual retry needed;
the comment still lands on the correct file. To target a file directly (skipping the line attempt),
omit `--line`:

```bash
gh-review comment --review-id PRR_... --path {file} --body '{body}'
```

File-level comments cannot carry `suggestion` blocks (suggestions need a line range). Use a `diff`
block with a line annotation instead, as described above.

### 5. Report

Output these sections in the conversation (not a file):

**PR:** use the `url` from the step 1 `gh pr view` JSON. Omit for commit-range and current-changes
reviews, which have no PR.

**Verdict:** approve, request changes, or comment-only, with a one-sentence rationale.

**Summary:**

- **Blockers:** critical issues preventing merge
- **Should fix before production:** serious but working issues
- **Recommendations:** non-urgent improvements

**Citations:**

List every source consulted to back findings. Each entry: the `ctx7` library ID and query, a file
path with line range from the worktree or repo, or a URL fetched via an approved tool this session.
No bracket indices, no carry-forward from prior sessions. If a claim could not be verified, list the
attempt and mark it `unverified`.

**Confidence:**

Rate overall confidence as `high`, `medium`, or `low` with a one or two sentence justification. Note
whether any finding rests on assumption rather than confirmed behavior. If not `high`, name the
weakest comments and why.

If minor issues were requested, add a **Medium and Low Priority** section before Citations.

## Rules

- MUST load the `gh-pr-review` skill before posting comments
- Use ```` ```suggestion ```` for code fixes on line-level comments; ```` ```diff ```` for
  file-level
- Include file paths and line numbers for every comment
- Do not submit the pending review; the user submits manually via GitHub UI
- Do not use TodoWrite or task tracking
- Do not clean up the worktree; leave it in `/tmp` for reference
- Do not create `pr-{number}-review-comments.ignored.md`; file-level fallback handles out-of-range
- Citations and Confidence sections are mandatory; a review without them is incomplete
