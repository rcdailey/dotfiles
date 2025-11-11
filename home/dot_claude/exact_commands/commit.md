---
allowed-tools: Bash(git diff:*), Bash(git commit:*), Bash(git add:*), Bash(git update-index:*), Bash(git reset:*)
description: Create git commits with flexible natural language instructions
---

# Git Commit Command

Execute with minimal output - only show final commit message(s).

**IMPORTANT**: Do not use TodoWrite or any todo/task management tools. Work directly without task
tracking.

**Performance**: Run independent commands in parallel when possible. Run dependent commands
sequentially.

## Systematic Workflows

Parse natural language instruction and execute corresponding workflow:

### Staged Workflow (`/commit`)

Commit only staged changes. DO NOT add any files.

- **Inspect**: `git diff --cached`
- **Act**: `git commit -m "message"` (NO git add commands)
- Fail if no staged changes exist

### All Workflow (`/commit all`)

Stage and commit all changes.

- **Inspect**:
  1. `git add -A`
  2. `git diff --cached`
- **Act**: `git commit -m "message"`

### Multi-commit Workflow (`/commit make multiple commits`)

Break changes into logical commits.

- **Inspect**:
  1. `git reset`
  2. `git add -N .`
  3. `git diff`
  4. `git reset`
- **Group changes** using these heuristics (priority order):
  1. File type separation: code, tests, docs, config files
  2. Directory boundaries: same directory/module
  3. Change type: refactoring, features, fixes, cleanup
  4. Dependency order: foundation changes before dependent changes
- **For each logical group**:
  1. `git add <files>` (includes deleted files - deletions are staged via `git add`)
  2. `git commit -m "message"`
  - Continue until all changes committed
- **IMPORTANT**: `git add <file>` works for deletions - it stages the removal to the index
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

**MANDATORY**: Examine actual diff content AND consider project context from CLAUDE.md before
creating commit messages. Use project context to correctly classify changes as affecting the
versioned artifact (`fix`/`feat`) vs tooling/infrastructure (`chore`/`ci`/`docs`). NEVER make
assumptions based on filenames, paths, or diff stats alone.

**Format**: Always use conventional commits format.

**Subject**: Imperative mood, lowercase type prefix, capitalize scope/description, no period, ≤50
chars. Test: "If applied, this commit will [subject line]"

**CRITICAL - Type Capitalization**: Conventional commit types MUST be lowercase. Examples:

- ✓ CORRECT: `feat(api): Add user endpoint`
- ✗ WRONG: `Feat(api): Add user endpoint`
- ✓ CORRECT: `fix: Resolve memory leak`
- ✗ WRONG: `Fix: Resolve memory leak`

**Types**: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert

**Body**: Focus on WHY changes were made, not what changed. Explain problem, motivation, context.
Use bullet points, wrap at 72 chars.

**Multi-line syntax**: `git commit -m "subject\n\nbody line 1\nbody line 2"`

## Project Context Inference

**CRITICAL:** Project CLAUDE.md is already loaded in your context. Use this information to inform
commit type decisions. DO NOT search for or read CLAUDE.md files - operate solely on project
knowledge already in context.

**Inference Process:**

1. Review CLAUDE.md content for project type indicators (e.g., "dotnet project", ".csproj files",
   "npm package", "Rust crate")
2. Identify what constitutes the "primary versioned artifact" vs ancillary tooling
3. Apply conventional commit semantics correctly:
   - `fix`/`feat`/`BREAKING CHANGE`: Changes to primary versioned artifact
   - `chore`: Changes to tooling, configs, dependencies that don't affect artifact
   - `ci`: CI/CD pipeline changes
   - `docs`: Documentation-only changes
   - `test`: Test-only changes

**Examples:**

- Dotnet project with renovate.json5 change → `chore` (config tooling, not library code)
- Node package with src/*.ts change → `fix` or `feat` (affects published package)
- Any project with .github/workflows change → `ci` (pipeline tooling)

**Uncertainty Protocol:**

If you cannot confidently determine the project's primary artifact from CLAUDE.md:

1. REFUSE to commit
2. Report: "Cannot determine project versioning scope from CLAUDE.md"
3. REQUEST user add project overview section describing:
   - Primary project type (library, application, tooling)
   - What gets versioned (npm package, docker image, binary, etc.)
   - Source code locations vs ancillary configs

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
