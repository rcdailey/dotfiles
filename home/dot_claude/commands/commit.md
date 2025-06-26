---
allowed-tools: Bash(git diff --cached), Bash(git commit -m), Bash(git add -A)
description: Create a git commit for staged changes only
---

## Context

- Staged changes: !`git diff --cached`

## Your task

Create a single git commit. Follow these rules:

1. **Check for --all flag**: If `$ARGUMENTS` contains "--all", stage all changes with `git add -A` first
2. **Default behavior**: Only commit what has been explicitly staged (never use `git add` unless --all flag is present)
3. **Analyze the staged changes** to understand what is being committed
4. **Draft a commit message** following the guidelines below
5. **Commit staged changes** using `git commit -m`
6. **Verify the commit** was successful
7. **Display the commit message** so you can see what was committed

## Commit Message Best Practices

### Subject Line (First Line)

- **Use imperative mood**: "Fix bug" not "Fixed bug" or "Fixes bug"
- **Capitalize first letter**: "Add feature" not "add feature"
- **No ending period**: "Update config" not "Update config."
- **72 characters maximum**: Keep it concise and readable
- **Complete this sentence**: "If applied, this commit will _[subject line]_"

### Body (Optional)

- **Separate from subject** with a blank line
- **Wrap at 72 characters** for readability
- **Explain the "why"** not just the "what"
- **Describe the problem** and how this change addresses it
- **Use bullet points** for multiple items with hanging indents

### Structure

```
Short summary (72 chars or less)

More detailed explanation if needed. Wrap lines at 72 characters.
Explain why this change is being made and what problem it solves.

- Use bullet points for multiple details
- Maintain hanging indentation
- Reference issues in body, not subject line
```

## Conventional Commits (Only if Repository Uses Them)

**Check first**: Look at recent commit history to determine if this repository follows conventional
commits.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Common Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, missing semicolons, etc.)
- `refactor:` - Code refactoring without feature changes
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks, dependency updates
- `build:` - Build system or external dependency changes
- `ci:` - CI/CD configuration changes

### Breaking Changes

- Add `!` after type: `feat!: redesign user interface`
- Or use footer: `BREAKING CHANGE: redesigned user interface`

### Examples

- `feat: add user authentication`
- `fix(api): handle null response in user endpoint`
- `docs: update installation instructions`
- `chore: update dependencies to latest versions`

## Important Notes

- **Never commit unstaged changes** - only commit what has been explicitly staged
- **Always verify changes** before committing by reviewing `git diff --cached`
- **Keep commits focused** - each commit should represent a single logical change
- **Test before committing** if applicable to ensure changes don't break functionality
- **Use present tense** in commit messages to describe what the commit does when applied
- **No Claude branding or metadata** - exclude any Claude Code attribution, signatures, or
  boilerplate text
- **No Co-Authored-By tags** - do not add Claude authorship attribution to commits
- **Clean commit messages only** - focus solely on the technical change being made
