---
allowed-tools: Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr checkout:*), Bash(gh issue view:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git stash:*), Bash(git switch:*), Bash(terraform -chdir:*), Read, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__get-library-docs, mcp__tavily__tavily-search
argument-hint: [pr-number or commit-range] [include medium/minor issues]
description: Code Review for PRs
---

# Comprehensive Code Quality Review

Perform comprehensive code quality review focusing on **critical and high-priority issues only**,
unless user requests medium/low priority issues.

## Command Arguments

Parse `$ARGUMENTS` to determine review scope:

- **PR number** (e.g., `#16` or `16`): Review pull request changes
- **Commit range** (e.g., `main..feature-branch`): Review commit range
- **Include minor issues**: Detect natural language like "include medium", "also include minor",
  "include low priority", "all issues", etc.
- **No arguments**: Review staged/unstaged changes in current repo

## Include Minor Issues Detection

Look for keywords/phrases in `$ARGUMENTS` that indicate user wants medium/low priority issues:

- "include medium", "include minor", "include low"
- "also medium", "also minor", "also low"
- "with medium", "with minor", "with low"
- "all issues", "all priorities", "everything"
- "medium too", "minor too", "low too"

If ANY of these patterns are detected, include medium and low priority issues in a separate section.

## Output Requirements

**CRITICAL**: Create a markdown file named `pr-{number}-review-comments.ignored.md` (for PRs) or
`code-review-{timestamp}.ignored.md` (for other reviews) in the repository root directory.

The markdown file MUST:

- Use GitHub-compatible markdown formatting
- Structure comments as copy-paste ready for GitHub PR reviews
- Include file paths and line numbers for each issue
- Use first-person, conversational tone (avoid AI-sounding language)
- Reserve fenced code blocks ONLY for actual code suggestions
- Focus on actionable, specific feedback

## Review Process

### 0. MANDATORY Working Copy Safety Check (PRs ONLY)

**ABSOLUTELY CRITICAL - VIOLATION WILL CAUSE DATA LOSS:**

Before ANY PR review operations, you MUST execute `git status --porcelain` and verify:

- ZERO output (no staged, unstaged, or untracked files)
- If ANY output exists, you MUST:
  1. IMMEDIATELY STOP all review operations
  2. Display the exact `git status` output to the user
  3. REFUSE to proceed with this error message:

```txt
CRITICAL ERROR: Working copy has uncommitted changes or untracked files.

PR checkout would overwrite or lose your work. You MUST clean up the working copy first:
- Commit changes: `git add -A && git commit`
- Stash changes: `git stash push -u -m "WIP before review"`
- Delete untracked: `git clean -fd` (DESTRUCTIVE - verify first)

Aborting review to prevent data loss.
```

**DO NOT:**

- Offer to stash automatically
- Suggest proceeding anyway
- Provide workarounds
- Minimize the severity of this check

**This is non-negotiable. Data loss prevention takes absolute priority.**

### 1. Context Gathering

Gather relevant information in parallel using multiple tool calls:

**For PRs:**

- `git status --porcelain` (MANDATORY safety check - see section 0)
- `gh pr view {number} --json title,body,files,additions,deletions`
- `gh pr view {number} --json comments --jq '.comments[] | select(.author.login == "rcdailey" or
  (.author.login | contains("robert-dailey")) | not) | {author: .author.login, path: .path, line:
  .line, body: .body}'`
- `gh pr checkout {number}` (only after working copy is confirmed clean)
- `gh pr diff {number}`

**For commits:**

- `git log {range} --oneline`
- `git diff {range}`

**For current changes:**

- `git status`
- `git diff HEAD`

### 2. Research and Analysis

Use context7 and tavily tools proactively to:

- Understand unfamiliar technologies, frameworks, or patterns
- Verify best practices for specific use cases
- Research security implications
- Validate architectural decisions

**Key principle**: Never assume or guess - always research when uncertain.

**Important**: With the PR checked out locally, you can now:

- Read actual files to understand full context
- Run tests to verify functionality
- Analyze dependencies and configuration
- Trace code paths beyond the diff

### 3. Review Categories

Analyze code across these dimensions, prioritizing critical and high-severity issues:

#### Security (Highest Priority)

- Credential exposure, hardcoded secrets
- SQL injection, XSS, CSRF vulnerabilities
- Authentication/authorization flaws
- Input validation gaps
- Encryption weaknesses

#### Architecture & Design (High Priority)

- Incorrect resource configuration
- Missing error handling
- Data loss risks
- Breaking changes in multi-environment setups
- Scalability concerns

#### Code Quality (High Priority)

- Code duplication (DRY violations)
- Logic errors and bugs
- Performance bottlenecks
- Missing required configurations

**Medium Priority** (only if `--include-minor` flag):

- Code organization improvements
- Documentation gaps
- Test coverage suggestions
- Minor refactoring opportunities

**Low Priority** (only if `--include-minor` flag):

- Code style inconsistencies
- Comment improvements
- Naming suggestions

### 4. Issue Identification

For each issue found:

- Assign severity: CRITICAL, HIGH, MEDIUM, LOW
- Note specific file path and line number
- Explain the problem in plain language
- Provide concrete, actionable recommendation
- Include code example when helpful

### 5. Generate Review Comments

Follow Google's code review best practices for writing comments. Each comment should:

- Explain the problem and why it matters
- Be conversational and kind (comment on code, not the developer)
- Provide concrete, actionable guidance
- Include code examples when helpful
- Avoid redundant observations about what changed

**Existing Comment Analysis:**

When existing comments from others (NOT 'rcdailey' or usernames containing 'robert-dailey') share
the same concern:

- **Add as follow-up ONLY if** you provide:
  - Additional technical details or research
  - Related issues in the same area
  - More severe implications they didn't mention
  - Concrete code suggestions they lacked

- **Create separate comment if** your concern is distinct even if in same file/area

- **Skip entirely if**:
  - You're just agreeing without new information
  - You would simply confirm or repeat what they already said
  - Your comment doesn't add meaningful value beyond their analysis

Create individual review comments with this simplified structure:

```txt
## Comment {N}: {Brief Title}

**File:** `{path}`
**Line:** {number}

{Conversational explanation of the issue explaining:
- What the problem is
- Why it matters (impact/consequences)
- Concrete recommendation or suggestion}

{Optional: fenced code block with suggested fix if helpful}
```

**For follow-up to existing comment:**

```txt
## Comment {N}: Follow-up to @username's comment

**File:** `{path}`
**Line:** {number}
**Related to:** @username's comment about {topic}

{Acknowledge their point briefly, then add your additional analysis/details/code}
```

Example good comment:

## Comment 1: Inconsistent Validation Between Request Types

**File:** `src/Client.Api/Cases/CaseValidators.cs` **Line:** 26

I noticed that `CaseRequestValidator` now validates `ProductCode` as required (line 21), but
`SequentialCaseRequestValidator` doesn't have the same validation rule. Since both request types
have the same `InterpretationRequest` property structure, they should have consistent validation.

This creates inconsistent API behavior between two similar endpoints and the OpenAPI spec shows both
endpoints have identical `interpretationRequest` structures.

I recommend adding the same validation rule to `SequentialCaseRequestValidator`:

```csharp
public class SequentialCaseRequestValidator : AbstractValidator<SequentialCaseRequest>
{
    public SequentialCaseRequestValidator()
    {
        RuleFor(x => x.Applicant).NotNull().SetValidator(new ApplicantValidator());
        RuleFor(x => x.InterpretationRequest.ProductCode).NotNull().NotEmpty();
    }
}
```

What to avoid:

- Separate "Problems", "Recommendation", "Impact" sections (redundant structure)
- Statements like "This should be fixed before merge" (let severity speak for itself)
- Restating what the developer already knows (e.g., "now changed from array to object")
- Multiple bullet lists when a paragraph works better

### 6. Markdown File Structure

**For files WITHOUT minor issues requested:**

```markdown
# PR #{number} Review Comments - Critical and High Priority Issues

Instructions: Navigate to the specified file and line in GitHub's PR review interface, click "Add a comment", and paste the comment text.

---

## Comment 1: {Title}
{comment content}

---

## Comment 2: {Title}
{comment content}

---

## Summary

**Total Issues:** {count} ({critical} Critical, {high} High Priority)

**Blockers for merge:**
1. {issue 1}
2. {issue 2}
...

**Overall Recommendation:** {Request changes|Approve with suggestions|Approve}
```

**For files WITH minor issues requested:**

Add this section at the bottom, after the summary:

```markdown
---

## Medium and Low Priority Issues (Optional Improvements)

These issues don't block the merge but could improve code quality:

### Medium Priority

## Comment {N}: {Title}
{comment content}

---

### Low Priority

## Comment {N}: {Title}
{comment content}
```

## Critical Rules

**DO:**

- Focus on critical and high-priority issues that block or should block merge
- Use context7 and tavily liberally to verify assumptions
- Write in first person with conversational tone
- Provide specific file paths and line numbers
- Include actionable recommendations with code examples
- Create the markdown file with `.ignored.md` extension in repo root

**DO NOT:**

- Include preamble or explanations before creating the file
- Use alarmist language or excessive severity labels
- Create overly formal or AI-sounding comments
- Assume knowledge - research unfamiliar concepts
- Include minor issues unless user requested them via natural language
- Use TodoWrite or task tracking tools
- Wrap entire comments in code blocks (only use for actual code)
- Use redundant structured sections (Problems/Recommendation/Impact)
- Add "this should be fixed before merge" statements
- Restate obvious facts about what changed in the PR
- Leave comments that simply confirm or repeat existing reviewer comments
- Add comments without meaningful new information or analysis

## Error Handling

- **Dirty working copy** (PRs only): ABORT immediately with critical error message (see section 0)
- **No PR found**: Report error and suggest valid PR numbers
- **No changes**: Report that there are no changes to review
- **Invalid arguments**: Explain valid argument formats
- **File creation fails**: Report error and suggest alternative location
- **PR checkout fails**: Report error and suggest manual checkout or checking PR state

## Example Usage

```bash
/code-review 16
/code-review #16 and also include medium
/code-review #123 include minor issues too
/code-review main..feature-branch with low priority
/code-review all issues
```
