---
description: Code review for PRs with GitHub-ready comments
---

Review code and create `pr-{number}-review-comments.ignored.md` in repo root with GitHub-ready
comments. Load the `gh-pr-review` skill for review etiquette and tooling reference.

Focus on critical/high priority issues unless $ARGUMENTS includes "medium", "minor", "low", or
"all". Bias toward fewer, higher-signal comments. A review with 2 critical findings is better than
one with 8 comments where 6 are nits.

## Argument Parsing

- PR number (e.g., `16` or `#16`): Review pull request
- Commit range (e.g., `main..feature`): Review commits
- No arguments: Review staged/unstaged changes
- Include "medium", "minor", "low", "all": Add lower priority issues section

## Process

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

Delegate existing comment collection to an explore subagent. The subagent should:

- Fetch both review comments and issue comments:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate
```

- Filter with jq: truncate any comment body over 500 chars, extract only author, path, line, and a
  short body snippet
- Skip dismissed review comments entirely
- For bot comments (any author ending in `[bot]`): keep only non-dismissed, line-specific feedback;
  discard walkthrough summaries, "resolved comments" lists, and any embedded state blobs or base64
  data
- For human comments: keep all, but still truncate bodies over 500 chars
- Return a consolidated, itemized summary (not raw JSON)

The subagent keeps the massive raw comment payloads out of this context window.

**For commits:** `git log {range} --oneline` and `git diff {range}`

**For current changes:** `git status` and `git diff HEAD`

### 2. Deduplicate Against Existing Comments

Before formulating feedback, cross-reference against the comment summary from the subagent. For each
potential comment:

- **Already covered adequately:** Omit it.
- **Covered but incomplete or incorrect:** Affirm the existing comment and add missing context.
  Reference who raised it.
- **Not yet raised:** Include it as a new comment.

The review file should only contain comments that add value beyond what's already on the PR.

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

### 4. Write Comments

Load the `humanizer` skill before creating the review file (not in parallel with file creation).
Apply the tone and etiquette guidelines from the `gh-pr-review` skill.

**Format:**

````markdown
## Comment {N}: {Brief title}

**File:** `{path}`
**Lines:** {start}-{end}

{Conversational explanation of the issue and why it matters. End with suggestion.}

```suggestion
{verbatim replacement for lines start through end}
```
````

The line range defines exactly which lines the suggestion block replaces. Do not include surrounding
context lines; they would be deleted when the suggestion is applied. For single-line comments, use
the same line for both start and end (e.g., `152-152`).

Do not hard-wrap prose paragraphs within a comment body. Each paragraph is a single unbroken line;
separate paragraphs with blank lines. GitHub's UI wraps at render time, and hard-wrapped source
produces awkward line breaks. Lists, code blocks, and `suggestion` blocks keep their normal line
structure.

### 5. File Structure

Write the review file to the **original repo root** (not the worktree).

```markdown
# PR #{number} Review Comments

---

## Comment 1: {title}
{content}

---

## Summary

**Blockers:** {critical issues preventing merge}

**Should fix before production:** {serious but working issues}

**Recommendations:** {non-urgent improvements}

## Citations

List every source consulted to back findings. Each entry: the `ctx7` library ID and query, a file
path with line range from the worktree or repo, or a URL fetched via an approved tool this session.
No bracket indices, no carry-forward from prior sessions. If a claim could not be verified, list
the attempt and mark it `unverified`.

## Confidence

Rate overall confidence in the review as `high`, `medium`, or `low`, then justify in one or two
sentences. Address: how thoroughly sources backed each finding, whether any comment rests on
pattern-matching rather than verified behavior, and the estimated hallucination risk. If confidence
is not `high`, enumerate which comments are weakest and why.
```

If minor issues requested, add section before Citations:

```markdown
---

## Medium and Low Priority Issues

### Medium Priority
{comments}

### Low Priority
{comments}
```

## Rules

- Create markdown file with `.ignored.md` extension
- Use ```` ```suggestion ```` format for code fixes
- Include file paths and line numbers
- Do not use TodoWrite or task tracking
- Do not clean up the worktree; leave it in `/tmp` for reference during comment posting
- Do not install dependencies, run tests, or run build commands unless a specific finding requires
  runtime verification
- Do not read README, docs, or wiki files unless a finding specifically needs them
- Do not delegate to the researcher subagent or use web search
- Do not fetch the full PR diff; use the changed file list and targeted local diffs
- Every finding that references a library, framework, language, tool, CLI, or standard MUST cite a
  `ctx7` lookup or a concrete file reference. Unverified claims MUST be reframed as questions.
- Citations and Confidence sections are mandatory; a review without them is incomplete
