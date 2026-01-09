---
name: git-commit
description: Conventional commit format, type selection, and commit best practices
---

## Conventional Commits

Format: `type(scope): Description`

Types: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert

Subject line:

- Max 72 characters (move details to body if needed)
- Type must be lowercase
- Imperative mood ("Add feature" not "Added feature")
- No trailing period

Body (when needed):

- Explain WHY, not what changed
- Hard-wrap at 72 characters
- Use `git commit -m "subject" -m "body"`

## Type Selection

Determine type from project context in AGENTS.md:

- Primary artifact changes (source code) -> feat/fix
- Tooling, config, dependencies -> chore
- CI/CD pipelines -> ci
- Documentation -> docs

If project type is unclear from AGENTS.md, ask before committing.

## Pre-commit Hooks

If commit fails due to hook auto-fixes:

1. Run `git update-index --again`
2. Retry the commit

If validation error: stop and report to user. Do not bypass hooks.

## Critical Rules

- Never run `git add` when not explicitly requested
- Examine actual diff content to determine type, not filenames
