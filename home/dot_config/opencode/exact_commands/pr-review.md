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

- `gh-scout prs {owner/repo} {number}` for PR metadata, description, and comments
- Follow linked issues, tickets, or PRDs referenced in the PR description or comments. Check the
  repo for product documentation (README, docs/, wiki) relevant to the changed areas. This context
  feeds the Background section of each comment.
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

For every potential comment, research both the technical claim and the domain context:

- Use Context7 to query relevant library/framework documentation
- Use web search or web fetch for official docs, security advisories, or language specs
- Check the project's own code for patterns that confirm or contradict your concern
- Read linked issues, PRDs, or product docs to understand the business context and user-facing
  behavior of the code being changed

Track which sources informed each comment. If you cannot find an authoritative source to back a
technical claim, either drop the comment or reframe it as an open question. Do not assert facts
based solely on training knowledge.

### 4. Write Comments

Load the `humanizer` skill before creating the review file (not in parallel with the file creation).
Apply the tone and etiquette guidelines from the `gh-pr-review` skill.

The review file serves two audiences. Mark sections clearly so the posting step knows what to
include.

**Format:**

````markdown
## Comment {N}: {Brief title}

**File:** `{path}`
**Line:** {number}

<!-- POST: Everything between POST markers is the GitHub comment body -->

{Conversational explanation of the issue and why it matters. End with
suggestion.}

```suggestion
{code fix if applicable}
```

<!-- /POST -->

**Background:** {Teach the reviewer about the product and codebase context
surrounding this comment. This section is for the reviewer's education, not
for the PR author. Write it so someone with no prior exposure to this area
of the product can follow the comment.

Lead with product context before implementation details. Follow this order:

1. What feature or area of the product is this? What does it do for users
   and why does it exist?
2. What business goal or user need is driving this change?
3. Any domain concepts or terminology needed to follow the discussion.
4. Only then: how the relevant code is structured and how components
   interact.

Do not assume the reviewer knows what any feature, entity, or workflow is.
Name it, explain its purpose, then connect it to the comment.

Draw from linked issues, PR description, PRDs, project documentation, README
files, external product docs, and broader codebase exploration. Keep it to a
short paragraph (3-5 sentences).}

**Sources:**

- {Each source that informed this comment and the background section: Context7
  doc queries, web search results, official documentation URLs, linked issues
  or PRDs, language/framework specs, or RFCs. Use "[Title](url)" for links.
  For project code, cite file path and line range. For issue trackers, link
  directly to the issue or ticket.}
````

- Content between `<!-- POST -->` and `<!-- /POST -->`: posted to GitHub as the review comment.
  Nothing outside these markers is posted.
- Background, Sources, file/line metadata: reviewer's eyes only. These stay in the local review
  file.
- Every comment MUST have both a Background and Sources section. Comments without verifiable sources
  must not be included in the review. If no authoritative source can be found for a concern, demote
  it to a question rather than an assertion (e.g., "I'm not sure if this is safe; worth checking the
  docs for [X]").

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
