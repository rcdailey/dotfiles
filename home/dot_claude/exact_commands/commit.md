---
allowed-tools: Bash(git diff:*), Bash(git commit:*), Bash(git add:*), Bash(git log:*), Bash(git update-index:*), Bash(git reset:*)
description: Create git commits with flexible natural language instructions
---

# Git Commit Command

Execute with minimal output - only show final commit message(s).

**IMPORTANT**: Do not use TodoWrite or any todo/task management tools. Work directly without task
tracking.

## Systematic Workflows

Parse natural language instruction and execute corresponding workflow:

### Staged Workflow (`/commit`)

Commit only staged changes. DO NOT add any files.

- **Inspect**: Use multiple parallel Bash tool calls:
  1. `git log --oneline -3 origin/HEAD` (or `git log --oneline -3 origin/master`)
  2. `git diff --cached`
- **Act**: `git commit -m "message"` (NO git add commands)
- Fail if no staged changes exist

### All Workflow (`/commit all`)

Stage and commit all changes.

- **Inspect**: Use multiple parallel Bash tool calls:
  1. `git log --oneline -3 origin/HEAD` (or `git log --oneline -3 origin/master`)
  2. `git add -A`
  3. `git diff --cached`
- **Act**: `git commit -m "message"`

### Multi-commit Workflow (`/commit make multiple commits`)

Break changes into logical commits.

- **Inspect**: Use multiple parallel Bash tool calls:
  1. `git log --oneline -3 origin/HEAD` (or `git log --oneline -3 origin/master`)
  2. `git reset`
  3. `git add -N .`
  4. `git diff`
  5. `git reset`
- **Group changes** using these heuristics (priority order):
  1. File type separation: code, tests, docs, config files
  2. Directory boundaries: same directory/module
  3. Change type: refactoring, features, fixes, cleanup
  4. Dependency order: foundation changes before dependent changes
- **For each logical group**:
  - **Act**: Use separate Bash tool calls:
    1. `git add <files>`
    2. `git commit -m "message"`
  - Continue until all changes committed
- Use `git add -p` for splitting changes within files
- Aim for 2-5 commits maximum

## Argument Parsing

- **No arguments**: Staged workflow (NO git add commands)
- **"all"**: All workflow
- **"make multiple commits"** or **"multiple commits"**: Multi-commit workflow
- **Custom instructions**: Parse and execute accordingly
- **Ambiguous input**: Default to staged workflow, ask for clarification

## Critical Rules

- **NEVER** run `git add` commands in staged workflow (no arguments)
- **ONLY** use `git add` when explicitly requested via "all" or multi-commit workflows

## Message Rules

**MANDATORY**: ALWAYS examine actual diff content before creating commit messages. NEVER make
assumptions based on filenames, paths, or diff stats alone.

**Format**: Use conventional commits ONLY if last 3 commits consistently use type prefixes.

**Subject**: Imperative mood, capitalize first letter, no period, ≤50 chars. Test: "If applied, this
commit will [subject line]"

**Types**: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert

**Body**: Focus on WHY changes were made, not what changed. Explain problem, motivation, context.
Use bullet points, wrap at 72 chars.

**Multi-line syntax**: `git commit -m "subject\n\nbody line 1\nbody line 2"`

## Pre-commit Hook Handling

When commit fails due to hooks:

1. **Auto-fixes**: Use separate Bash tool calls:
   - `git update-index --again`
   - `git commit -m "message"`
2. **Validation errors**: Stop and report to user
3. **No modifications**: Report hook validation failure

Never manually fix code issues or bypass hook requirements.

## Error Handling

- **No changes**: Stop and report status
- **Detached HEAD**: Warn user, suggest creating branch
- **Merge conflicts**: Stop immediately
- **No repository**: Verify working directory is git repo
- **Hook failures**: Follow pre-commit protocol
