---
allowed-tools: Bash(git diff:*), Bash(git commit:*), Bash(git add:*), Bash(git log:*), Bash(git update-index:*)
description: Create git commits with flexible natural language instructions
---

# Flexible Git Commit Command

- Current changes: !`git diff --name-status`

## Execution Protocol

**SILENT MODE**: Execute with minimal output - only show final commit message(s).

**BATCH OPERATIONS**: Use efficient 2-command pattern:

1. **Analysis**: `git log --oneline -3 && [git add -A &&] git diff --cached` (skip `add -A` for
   staged-only)
2. **Execution**: `git commit -m "message"` (no chaining)

Never use `git status` - diff output contains all needed file information.

**MANDATORY DIFF ANALYSIS**: ALWAYS examine actual code changes with `git diff` before creating
commits. NEVER commit based solely on filenames, diff stats, or assumptions.

## Argument Parsing

Parse the natural language instruction provided after `/commit`:

- **No arguments** (just `/commit`): Commit only staged changes
- **"all"**: Stage all changes (`git add -A`) then commit
- **"make multiple commits"** or **"multiple commits"**: Interactive staging workflow to break work
  into logical commits
- **Custom instructions**: Parse human-readable descriptions and execute accordingly
- **Ambiguous input**: Default to staged-only commit workflow and ask for clarification

## Task Flow

1. **Parse instruction**: Determine workflow from natural language argument
2. **Analysis command**: `git log --oneline -3 && [git add -A &&] git diff --cached`
3. **Analyze output**: Read log for commit style, read diff for actual code changes
4. **Generate commit message**: Based on actual code understanding and detected commit style
5. **Execution command**: `git commit -m "message"`
6. **Handle hook failures**: If failed, retry with `git update-index --again && git commit -m
   "message"`

## Workflows

### Default Workflow (no arguments)

- Analysis: `git log --oneline -3 && git diff --cached`
- Execution: `git commit -m "message"`
- Fail if no staged changes exist

### "all" Workflow

- Analysis: `git log --oneline -3 && git add -A && git diff --cached`
- Execution: `git commit -m "message"`

### Multiple Commits Workflow

- Examine actual diff content with `git diff` to understand all changes
- Group related changes using these heuristics (in priority order):
  1. File type separation: Keep code, tests, docs, config files in separate commits
  2. Directory boundaries: Group changes within same directory/module
  3. Change type: Separate refactoring, new features, bug fixes, cleanup
  4. Dependency order: Commit foundation changes before dependent changes
- For each logical group:
  - Stage specific files or patches using `git add <files>` or `git add -p`
  - Use `git diff --cached` to verify what is being committed
  - Generate appropriate commit message based on actual staged code changes
  - Commit the group
  - Continue until all changes are committed
- Use interactive staging (`git add -p`) for splitting changes within single files
- Aim for 2-5 commits maximum to maintain clarity

## Examples

- `/commit` → Commit staged changes only
- `/commit all` → Stage all changes, then commit
- `/commit make multiple commits` → Break changes into logical commits
- `/commit just the tests` → Stage and commit only test files

## Message Rules

**Format**: Check recent commits - use conventional commits ONLY if last 3 commits consistently use
type prefixes

**Subject**: Imperative mood, capitalize first letter, no period, ≤50 chars. Test: "If applied, this
commit will [subject line]"

**Types**: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert (only if repo uses
conventional commits)

**Body**: Focus on WHY changes were made, not what code was changed. Explain the problem being
solved, motivation, and context. What changed is visible in the diff. Use bullet points, wrap at 72
chars

**Content**: Be direct, eliminate filler words, don't assume reader knows context. Avoid subjective
assessments or value judgments - stick to objective technical facts

**Multi-line syntax**: Use single -m with embedded newlines: `git commit -m "subject\n\nbody line
1\nbody line 2"`

## Rules

- Follow workflow based on natural language instruction
- ALWAYS examine actual diff content before creating commit messages
- NEVER make assumptions based on filenames, paths, or diff stats alone
- Use conventional commits ONLY if last 3 commits consistently have type prefixes
- No Claude attribution or metadata
- Always validate changes exist before attempting commits

## Pre-commit Hook Handling

When commit fails due to pre-commit hooks:

1. **First failure with auto-fixes**: Chain `git update-index --again && git commit -m "message"` to
   re-stage hook modifications and retry
2. **Second failure or validation errors**: Stop and report to user
3. **No modifications detected**: Report hook validation failure

**Critical**: Always re-stage hook-modified files using `git update-index --again` before retry.

Never manually fix code issues or bypass hook requirements.

## Error Scenarios

- No changes: Stop and report status
- Detached HEAD: Warn user, suggest creating branch
- Merge conflicts: Stop immediately
- No repository: Verify working directory is git repo
- Permission errors: Report specific issue
- Hook failures: Follow pre-commit protocol
