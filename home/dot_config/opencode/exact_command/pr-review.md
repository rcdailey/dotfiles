---
description: Code review for PRs with GitHub-ready comments
---

Review code and create `pr-{number}-review-comments.ignored.md` in repo root with GitHub-ready
comments. Focus on critical/high priority issues unless $ARGUMENTS includes "medium", "minor",
"low", or "all".

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

- `gh pr view {number} --json title,body,files,additions,deletions`
- `gh pr checkout {number}`
- `gh pr diff {number}`

For commits: `git log {range} --oneline` and `git diff {range}`

For current changes: `git status` and `git diff HEAD`

### 3. Analyze

Use Context7 and web search to verify unfamiliar patterns, best practices, and security
implications. With PR checked out, read full files to understand context beyond the diff.

Review categories (priority order):

- **Security**: Credentials, injection, auth flaws, input validation
- **Architecture**: Resource config, error handling, data loss risks, breaking changes
- **Code quality**: Duplication, logic errors, performance, missing config

Medium/low (only if requested): Organization, docs, test coverage, style, naming

### 4. Write Comments

For each issue, verify every technical claim with Context7/web search before writing.

**Tone:**

- Bugs/defects: Direct language ("I think this is a bug...", "This will cause...")
- Style/architecture: Questions ("What do you think about...", "Would it make sense to...")
- Use contractions, be conversational, comment on code not developer

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

Skip comments that just repeat what other reviewers already said.

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
