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

### 1. Safety Check (PRs only)

Run `git status --porcelain`. If ANY output exists, abort with:

```txt
Working copy has uncommitted changes. Clean up before PR checkout:
- Commit: git add -A && git commit
- Stash: git stash push -u -m "WIP"
- Clean: git clean -fd (destructive)
```

### 2. Gather Context

For PRs (after safety check passes):

- `gh-scout prs {owner/repo} {number}` for PR metadata and comments
- `gh pr checkout {number}`
- `gh pr diff {number}`

For commits: `git log {range} --oneline` and `git diff {range}`

For current changes: `git status` and `git diff HEAD`

### 3. Analyze

With PR checked out, read full files to understand context beyond the diff. Apply the review
priorities and verification rules from the `gh-pr-review` skill.

### 4. Write Comments

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
