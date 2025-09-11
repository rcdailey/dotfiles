---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git show:*), Bash(pwd:*), Read, Write, Edit, Glob
argument-hint: [changes-scope] [optional-context]
description: Add entries to CHANGELOG.md following keepachangelog.com format
---

# Changelog Entry Command

Execute with minimal output - show complete diffs only.

**IMPORTANT**: Do not use TodoWrite or any todo/task management tools. Work directly without task
tracking.

## Keep a Changelog Format (EMBEDDED)

### Structure Requirements

- File: `CHANGELOG.md` in git repository root
- Format: Markdown with H2 version sections
- Date format: YYYY-MM-DD (ISO 8601 only)
- Latest version first (reverse chronological)
- Unreleased section at top for upcoming changes

### Change Types (MANDATORY CATEGORIES)

Use exact ordering shown below for the sections.

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

### Version Format Examples

```md
## [Unreleased]

### Added

- New feature description

### Fixed

- Fixed bug

## [1.2.0] - 2023-12-01

### Fixed

- Bug fix description
```

## Workflow

### Input Analysis

Parse $ARGUMENTS for changes scope:

- **Commits**: "commit abc123", "commits abc123..def456", "last 3 commits"
- **Working copy**: "working copy", "staged changes", "current changes"
- **Diff context**: "previous diff", "last diff in context"
- **Optional context**: Additional explanation after changes scope

### Change Analysis Steps

**MANDATORY: Use parallel Bash tool calls:**

1. `pwd` - Verify working directory
2. `git status` - Check repository state
3. Based on scope, execute ONE of:
   - **Commits**: `git show --stat --oneline <commit-range>`
   - **Working copy**: `git diff HEAD --stat`
   - **Staged**: `git diff --cached --stat`

### Commit Message Analysis

When analyzing commits, **CRITICAL**:

- Parse commit messages for intent/why understanding
- Look for conventional commit patterns (feat:, fix:, etc.)
- Extract business context beyond code changes
- Identify breaking changes, deprecations

### CHANGELOG.md Location

**MANDATORY**: Find CHANGELOG.md in git repository root:

1. Use `pwd` to get current directory
2. Navigate to git root if needed
3. Look for existing CHANGELOG.md
4. Create if missing with proper structure

### Entry Creation Logic

**Categorization Rules** (Apply in order):

1. **Added**: New features, APIs, functionality
1. **Changed**: Behavior modifications, API changes
1. **Deprecated**: Deprecation announcements
1. **Removed**: Feature removals, API deletions
1. **Fixed**: Bug fixes, error corrections
1. **Security**: Vulnerability fixes, security improvements

**Entry Format** (EXACT):

```md
- Brief description (max 80 chars, imperative mood)
```

**Unreleased Section Management**:

- Add entries to existing "## [Unreleased]" section
- Create section if missing
- Maintain proper H3 subsections for change types
- Keep entries in logical order within categories

### Diff Display

**MANDATORY**: After updating CHANGELOG.md, show complete diff:

- Use `git diff CHANGELOG.md` or equivalent
- Display full context of changes made
- Verify proper formatting and structure

## Argument Examples

- `/changelog last 2 commits` - Analyze last 2 commits
- `/changelog working copy refactoring database layer` - Analyze working copy with context
- `/changelog commit abc123 security fix` - Analyze specific commit
- `/changelog staged changes` - Analyze staged changes only

## Error Handling

- **No git repo**: Report error, exit
- **No CHANGELOG.md**: Create with proper header structure
- **Invalid commit range**: Report error with valid formats
- **No changes found**: Report no entries to add

## Critical Rules

- **NEVER** make assumptions about change categorization - analyze actual code changes
- **ALWAYS** examine diff content, not just filenames or paths
- **PRESERVE** existing CHANGELOG.md structure and formatting
- **MAINTAIN** chronological order (latest first)
- **USE** imperative mood for entries ("Add feature" not "Added feature")
