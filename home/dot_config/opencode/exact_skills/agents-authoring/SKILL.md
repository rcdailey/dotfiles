---
name: agents-authoring
description: Use when creating or updating AGENTS.md files
---

# AGENTS.md Authoring

Load this skill when creating or updating AGENTS.md files.

## Research Foundation

This guidance synthesizes:

- [agents.md](https://agents.md) - Open standard used by 60k+ projects, stewarded by Agentic AI
  Foundation under Linux Foundation
- GitHub's analysis of 2,500+ repositories with agents.md files
- Anthropic's context engineering documentation
- OpenAI Codex custom instructions guide
- Devin AI's good vs bad instructions documentation
- Builder.io's AGENTS.md best practices guide

## Core Concept

AGENTS.md is a "README for agents" - a dedicated, predictable place for AI coding agent context.
Supported by: OpenAI Codex, Google Jules, Cursor, VS Code, GitHub Copilot, Devin, Windsurf,
OpenCode, Aider, and many others.

## Essential Sections

Every AGENTS.md should cover:

### 1. Dos and Don'ts (Constraints)

Be nitpicky. Clear guidelines prevent repeated mistakes.

````markdown
### Do
- use TypeScript strict mode
- use functional components with hooks
- default to small, focused diffs

### Don't
- do not hard code colors - use design tokens
- do not add dependencies without approval
````

### 2. File-Scoped Commands

Prefer file-specific commands over project-wide. Faster feedback, fewer wasted cycles.

````markdown
### Commands
# Type check single file (seconds, not minutes)
npm run tsc --noEmit path/to/file.tsx

# Lint single file
npm run eslint --fix path/to/file.tsx

# Test single file
npm run vitest run path/to/file.test.tsx

# Full build only when explicitly requested
npm run build
````

### 3. Safety and Permissions

Explicit allow/ask lists prevent surprises.

````markdown
### Permissions
Allowed without asking:
- read files, list directories
- type check, lint, format single files
- run single unit tests

Ask first:
- package installs
- git push
- deleting files
- full build or E2E suites
````

### 4. Project Structure Hints

A tiny index saves exploration time every session.

````markdown
### Structure
- routes: `src/App.tsx`
- components: `src/components/`
- design tokens: `src/lib/theme/tokens.ts`
- API client: `src/api/client.ts`
````

### 5. Good/Bad Example Pointers

Point to real files. Examples beat abstractions.

````markdown
### Examples
Copy these patterns:
- forms: `src/components/UserForm.tsx`
- data fetching: `src/hooks/useProjects.ts`

Avoid these (legacy):
- class components like `src/legacy/Admin.tsx`
````

### 6. When Stuck Guidance

Escape hatch for uncertainty.

````markdown
### When stuck
- ask a clarifying question
- propose a short plan
- open a draft PR with notes
- do not push large speculative changes
````

### 7. PR/Commit Checklist

Define "ready" explicitly.

````markdown
### PR checklist
- lint, type check, tests: all green
- diff is small and focused
- brief summary of what changed and why
````

## Nested AGENTS.md for Monorepos

Place AGENTS.md in subdirectories for package-specific rules. Agent reads closest file to edited
code. Root file provides defaults; nested files override.

```txt
/root
  AGENTS.md           # Project-wide defaults
  /packages/legacy
    AGENTS.md         # React 17 rules for this package
  /packages/new-app
    AGENTS.md         # React 18 rules for this package
```

## Anthropic Context Engineering Principles

### Clarity at the Right Altitude

- Specific enough to guide behavior effectively
- Flexible enough to provide strong heuristics
- Not so detailed it becomes brittle

### Minimality

- Minimal set of information that fully outlines expected behavior
- Minimal does NOT mean short - it means only necessary information
- Remove redundancy ruthlessly

### Structure

- Organize into distinct sections
- Group related rules together
- Use consistent formatting

## Rule Writing Guidelines

### RFC 2119 Style for Maximum Compliance

Use RFC 2119 keywords (MUST, SHALL, SHOULD, MAY) for directives. LLMs parse these as strict
requirement levels. This produces measurably higher compliance rates than softer phrasing.

**Keyword semantics:**

- **MUST / REQUIRED / SHALL**: Absolute requirement. No exceptions.
- **MUST NOT / SHALL NOT**: Absolute prohibition. No exceptions.
- **SHOULD / RECOMMENDED**: Strong preference. Valid exceptions exist but require justification.
- **SHOULD NOT / NOT RECOMMENDED**: Strong discouragement. Valid exceptions require justification.
- **MAY / OPTIONAL**: Truly discretionary.

**Application:**

- Use MUST/MUST NOT for safety, correctness, and non-negotiable constraints
- Use SHOULD/SHOULD NOT for best practices where context may warrant deviation
- Use MAY sparingly; if something is truly optional, consider omitting it entirely

### Format: Constraint + Consequence

Bad: "Don't commit directly to main"

Good: "MUST NOT commit directly to main - use feature branches and PRs"

### Prefer Positive Over Negative

Bad: "MUST NOT use var"

Good: "MUST use `const` by default, `let` when reassignment needed (NEVER `var`)"

### Be Specific, Not Vague

Bad: "Be careful with error handling"

Good: "All async functions MUST have try/catch - unhandled rejections crash the process"

### Use Examples Over Adjectives

Bad: "Write concise commit messages"

Good: "Format: `fix(auth): handle expired tokens`, `feat(api): add search endpoint`"

## Antipatterns

| Antipattern                       | Problem                   | Fix                           |
|-----------------------------------|---------------------------|-------------------------------|
| Verbose explanations              | Wastes tokens             | Terse rule + consequence      |
| Repeated rules                    | Inconsistency risk        | Single authoritative location |
| Vague adjectives                  | Subjective interpretation | Concrete criteria or examples |
| Embedded discoverable info        | Stale, bloated            | Point to source (--help)      |
| Prohibitions without alternatives | No guidance on what TO do | Include correct approach      |
| Project-wide commands only        | Slow feedback loops       | File-scoped commands          |

## Good vs Bad Instructions (Devin Research)

### Good Instructions

- Name specific files/components
- Reference existing code as templates
- Include clear success criteria
- Define verification steps

Example: "Create endpoint `/users/stats` returning JSON. Reference `/orders/stats` in
`statsController.js` for structure. Add tests to `StatsController.test.js`."

### Bad Instructions

- Vague ("make it user-friendly")
- No specific components mentioned
- Unclear validation criteria
- Open-ended scope

Example: "Add a user stats endpoint." (No format, source, tests, or reference)

## Maintenance

Update AGENTS.md when:

- New constraints or coding standards are adopted
- Infrastructure or tooling changes
- Command syntax changes
- Project structure evolves

Process:

1. Identify what changed and why
2. Update the authoritative location (not duplicates)
3. Verify no contradictions introduced
4. Validate formatting (markdownlint)

## Validation Checklist

Before finalizing changes:

- [ ] Each constraint has a consequence
- [ ] Commands are copy-pasteable and file-scoped where possible
- [ ] Examples reference real files (not invented)
- [ ] "When stuck" guidance included
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
