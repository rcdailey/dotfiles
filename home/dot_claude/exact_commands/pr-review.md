---
allowed-tools: Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr checkout:*), Bash(gh issue view:*), Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git stash:*), Bash(git switch:*), Bash(terraform -chdir:*), Read, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
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
- Use GitHub suggestion format (```suggestion) for all code suggestions
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

Use context7 and exa tools proactively to:

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

**Factual Verification - MANDATORY FOR EVERY COMMENT:**

**CRITICAL WORKFLOW:** For EACH review comment you plan to write, you MUST:

1. **STOP before writing** - Identify every technical claim in your planned comment
2. **Research ALL claims** using context7 and exa:
   - Library/framework behavior and API usage patterns
   - Language syntax requirements and constraints
   - Tool-specific rules (Terraform, SQL, etc.)
   - Best practices and recommended patterns for the technology
   - Security implications and common vulnerabilities
   - Expected outcomes and failure modes
3. **Validate suggestions** - Test that your proposed fix/approach actually works
4. **Document sources** - Note which docs/resources validated your claims
5. **Only then write** - Compose comment using verified facts, not assumptions

**EVIDENCE REQUIREMENTS:**

- Every "this will cause X" claim needs context7/exa verification showing it causes X
- Every "must be Y" statement needs docs showing Y is required
- Every "best practice is Z" needs sources confirming Z is the standard approach
- When docs conflict or are unclear, explicitly state uncertainty in the comment

**DO NOT:**

- Make claims based on pattern recognition alone ("I've seen this before")
- Assume behavior without checking current docs (versions change)
- Trust memory over fresh research (your training data may be outdated)
- Write comments without completing verification steps above

**If you cannot verify a claim:** Either research deeper or soften language to indicate uncertainty
("I'm not certain, but this might...", "Based on similar patterns, this could...").

**Writing Style - CRITICAL:**

Comments must sound humble, approachable, and conversational - like a colleague suggesting ideas
rather than directing changes. Follow these voice patterns:

**Language patterns for BUGS/DEFECTS (objective problems):**

- "I think this is a bug because..." or "This looks broken..."
- "I'd recommend fixing..." or "This should probably be fixed..."
- "This will cause [specific problem]..." when the outcome is predictable
- Direct statements about objective issues are appropriate

**Language patterns for STYLE/ARCHITECTURE (subjective choices):**

- "What do you think about..." for alternative approaches
- "Would it make sense to..." for design suggestions
- "What if we..." for exploring options
- "This could..." when suggesting improvements
- Frame as questions to invite discussion on subjective matters

**Language patterns to AVOID:**

- Demanding language ("must", "needs to", "fix this immediately")
- Imperative verbs without context ("Change that", "Remove this")
- Absolute language without justification ("always", "never", "definitely")
- Treating bugs like opinions ("What do you think about fixing this crash?")

**Tone guidelines:**

- Be conversational and kind (comment on code, not the developer)
- Present observations as collaborative discussion points
- Use contractions naturally (it's, won't, doesn't)
- Keep sentences simple and direct
- Show humility about your suggestions

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
## Comment {N}: {Brief, conversational title}

**File:** `{path}`
**Line:** {number}

{Direct explanation of what you noticed, written conversationally. Explain the problem and why it
matters, using humble language. End with a suggestion framed as a question or collaborative idea.}

{Optional: GitHub suggestion block with suggested fix if helpful - use ```suggestion format}
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

## Comment 1: Inconsistent validation between request types

**File:** `src/Client.Api/Cases/CaseValidators.cs` **Line:** 26

I noticed that `CaseRequestValidator` now validates `ProductCode` as required (line 21), but
`SequentialCaseRequestValidator` doesn't have the same validation rule. Since both request types
have the same `InterpretationRequest` property structure, this could create inconsistent API
behavior between the two endpoints.

What do you think about adding the same validation rule to `SequentialCaseRequestValidator`?

```suggestion
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

- Demanding language ("This must be fixed", "You should change this")
- Strong declarations ("This will fail", "This causes problems")
- Formal phrasing ("I recommend that...", "It is advisable to...")
- Separate "Problems", "Recommendation", "Impact" sections (redundant structure)
- Restating what the developer already knows (e.g., "now changed from array to object")
- Multiple bullet lists when a paragraph works better

### 6. Markdown File Structure

**For files WITHOUT minor issues requested:**

```markdown
# PR #{number} Review Comments

---

## Comment 1: {Brief, conversational title}
{comment content using humble, approachable language}

---

## Comment 2: {Brief, conversational title}
{comment content using humble, approachable language}

---

## Summary

**Blockers:**

- Comment {N}: {Brief description}
- Comment {N}: {Brief description}

**Should fix before production:**

- Comment {N}: {Brief description}
- Comment {N}: {Brief description}

**Recommendations:**

- Comment {N}: {Brief description}
- Comment {N}: {Brief description}
```

Note: Use "Blockers" for critical issues that prevent the code from working, "Should fix before
production" for serious issues that work but have operational problems, and "Recommendations" for
improvements that aren't urgent.

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
- Use context7 and exa to factually verify EVERY technical claim before writing comments
- Research syntax requirements, API behavior, and best practices for technologies you're reviewing
- Write with humble, approachable language as if suggesting ideas to a colleague
- Use conversational tone with contractions (it's, won't, doesn't)
- Use direct language for bugs/defects ("I recommend...", "This will fail...") and questions for
  subjective choices ("What do you think about...", "Would it make sense to...")
- Provide specific file paths and line numbers
- Include actionable code examples when helpful using GitHub suggestion format (```suggestion)
- Create the markdown file with `.ignored.md` extension in repo root
- Keep comment titles brief and conversational (lowercase)

**DO NOT:**

- Include preamble or explanations before creating the file
- Use demanding language without justification ("must fix immediately", "needs to change now")
- Treat objective bugs as subjective opinions ("What do you think about this null pointer crash?")
- Use formal phrasing ("It is advisable to...", "One should...")
- Use alarmist language or excessive severity labels
- Create overly formal or AI-sounding comments
- Assume knowledge - research unfamiliar concepts
- Include minor issues unless user requested them via natural language
- Use TodoWrite or task tracking tools
- Use generic code blocks for suggestions (always use ```suggestion format instead)
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
