---
allowed-tools: Bash(git diff:*), Bash(git commit:*), Bash(git add:*), Bash(git status:*), Bash(git log:*)
description: Create a git commit for staged changes only
---

# Commit Staged Changes

- Staged changes: !`git diff --cached`

## Execution Protocol

**SILENT MODE**: Execute with minimal output - only show final commit message.

**BATCH OPERATIONS**: Use chained git commands in single tool calls:

- Analysis: `git diff --cached && git log --oneline -3`
- Commit: `git commit -m "subject line

body line 1 body line 2"`

## Task Flow

1. **Parse arguments**: Extract `--all` flag and `--why "message"` context
2. **Stage if needed**: Run `git add -A` only if `--all` present
3. **Analyze changes**: Use batched command for diff analysis and repo style detection
4. **Detect commit style**: Check if last 3 commits ALL have type: prefixes - if yes, use
   conventional commits, if no, use standard imperative
5. **Generate commit message**: Follow rules below, incorporate `--why` context if provided
6. **Commit**: Use simple git commit command
7. **Handle hook failures**: If pre-commit hooks modify files, stage the changes and retry commit

## Message Rules

**Format**: Check recent commits - use conventional commits ONLY if last 3 commits consistently use
type prefixes

**Subject**: Imperative mood, capitalize first letter, no period, ≤50 chars

**Types**: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert (only if repo uses
conventional commits)

**Body**: Answer journalist questions - what changed specifically, why was it needed, what effect
does it have? Use bullet points, wrap at 72 chars

**Content**: Be direct, eliminate filler words, don't assume reader knows context. Avoid
subjective assessments or value judgments - stick to objective technical facts

**Multi-line syntax**: Use single -m with embedded newlines: `git commit -m "subject\n\nbody line
1\nbody line 2"`

## Rules

- Only commit staged changes (unless `--all` flag)
- Use `--why` context to inform message, don't copy directly
- Detect commit style: use conventional commits ONLY if last 3 commits consistently have type:
  prefixes
- No Claude attribution or metadata
- Focus on technical change description

## Pre-commit Hook Handling

**Scope**: Only handle automatic hook fixes - do NOT manually fix code issues

If commit fails due to pre-commit hooks:

1. **First failure with auto-fixes**: Stage hook-modified files and retry commit once
2. **Second failure**: Stop and report to user - do not attempt manual fixes
3. **No auto-fixes**: Stop immediately - user must resolve hook errors manually

**Never**:

- Manually fix linting/formatting issues
- Modify code to satisfy hooks
- Override or bypass hook requirements
- Make multiple retry attempts beyond one auto-fix retry
