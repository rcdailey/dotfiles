---
description: Code review for PRs with GitHub-ready comments
---

Review code and create `pr-{number}-review-comments.ignored.md` in repo root with GitHub-ready
comments. Load the `gh-pr-review` skill for review etiquette and tooling reference.

Focus on critical/high priority issues unless $ARGUMENTS includes "medium", "minor", "low", or
"all".

## Argument Parsing

- PR number (e.g., `16` or `#16`): Review pull request
- Commit range (e.g., `main..feature`): Review commits
- No arguments: Review staged/unstaged changes
- Include "medium", "minor", "low", "all": Add lower priority issues section

## Process

### 1. Gather Context

**For PRs:**

- `gh-scout prs {owner/repo} {number}` for PR metadata and comments
- Fetch the PR head ref and create a detached worktree. If a worktree from a previous review of the
  same PR exists, remove it first:

```bash
git worktree remove --force /tmp/pr-review-{number} 2>/dev/null
git fetch origin pull/{number}/head &&
  git worktree add --detach /tmp/pr-review-{number} FETCH_HEAD
```

- The worktree is a bare checkout with no installed dependencies. If the project has a dependency
  manifest (e.g., `package.json`, `go.mod`, `requirements.txt`, `*.csproj`), run the appropriate
  install command in the worktree so analysis tools, linters, and type checkers work.

- `gh pr diff {number}`

Note the worktree path (`/tmp/pr-review-{number}`) for file reads in the analysis step. The worktree
is left in place after the review so you can reference files while posting comments.

- Fetch existing comments from both sources:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
```

```bash
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate
```

The first returns review comments on specific diff lines; the second returns conversation-level
comments (including bot output). Catalog the topics, files, and lines already covered.

**For commits:** `git log {range} --oneline` and `git diff {range}`

**For current changes:** `git status` and `git diff HEAD`

### 2. Deduplicate Against Existing Comments

Before formulating your own feedback, cross-reference the diff analysis against the existing comment
catalog. For each potential comment:

- **Already covered adequately:** Omit it. Don't restate what a bot or reviewer already said.
- **Covered but incomplete or incorrect:** Affirm the existing comment and add the missing context.
  Reference who raised it (e.g., "Building on @dependabot's note about...").
- **Not yet raised:** Include it as a new comment.

The review file should only contain comments that add value beyond what's already on the PR.

### 3. Analyze

Read full files from the worktree path (or current working copy for non-PR reviews) to understand
context beyond the diff. Apply the review priorities and verification rules from the `gh-pr-review`
skill.

### 4. Write Comments

Load the `humanizer` skill before creating the review file (not in parallel with the file creation).
Apply the tone and etiquette guidelines from the `gh-pr-review` skill.

**Format:**

````markdown
## Comment {N}: {Brief title}

**File:** `{path}`
**Line:** {number}

{Conversational explanation of the issue and why it matters. End with suggestion.}

```suggestion
{code fix if applicable}
```
````

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
```

If minor issues requested, add section at end:

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
- Use `\`\`\`suggestion` format for code fixes
- Include file paths and line numbers
- Do not use TodoWrite or task tracking
- Do not clean up the worktree; leave it in `/tmp` for reference during comment posting
