---
name: git-commit
description: Conventional commit format, type selection, and commit best practices
---

## Conventional Commits

Format: `type(scope): description`

Types: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert

## Line Length (Enforced by commitlint)

All limits are strictly enforced. Commits exceeding these limits will be rejected.

- Subject line: max 72 characters (including type/scope prefix)
- Body lines: max 72 characters each
- Footer lines: max 72 characters each

## Subject Line

- Max 72 characters total
- Type must be lowercase
- Imperative mood ("add feature" not "added feature")
- No trailing period
- No capitalization after colon

## Body (when needed)

- Separate from subject with blank line
- Explain WHY, not what changed
- Hard-wrap each line at 72 characters
- Use multiple `-m` flags: `git commit -m "subject" -m "body paragraph"`

## Type Selection

Determine type from project context in AGENTS.md:

- Primary artifact changes (source code) -> feat/fix
- Tooling, config, dependencies -> chore
- CI/CD pipelines -> ci
- Documentation -> docs

If project type is unclear from AGENTS.md, ask before committing.

## Hook Failures

If commit is rejected by commitlint:

1. Read the error message carefully
2. Fix the specific violation (usually line length)
3. Retry with corrected message

If commit fails due to pre-commit hook auto-fixes:

1. Run `git update-index --again`
2. Retry the commit

If validation error: stop and report to user. Do not bypass hooks.

## Critical Rules

- Never run `git add` when not explicitly requested
- Examine actual diff content to determine type, not filenames
- If a line would exceed 72 chars, break it before that point
