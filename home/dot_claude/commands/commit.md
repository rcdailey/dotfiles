---
allowed-tools: Bash(git diff --cached), Bash(git commit -m), Bash(git add -A)
description: Create a git commit for staged changes only
---

## Context

- Staged changes: !`git diff --cached`

## Your task

Create a single git commit. Follow these rules:

1. **Check for --all flag**: If `$ARGUMENTS` contains "--all", stage all changes with `git add -A` first
2. **Check for --why flag**: If `$ARGUMENTS` contains `--why "message"`, extract the quoted message as additional context about WHY this change was made (this is NOT the final commit message)
3. **Default behavior**: Only commit what has been explicitly staged (never use `git add` unless --all flag is present)
4. **Analyze the staged changes** to understand WHAT is being committed
5. **Combine analysis**: Use both the diff analysis (WHAT) and any `--why` context to understand the full picture
6. **Draft YOUR OWN commit message** following the guidelines below - DO NOT use the `--why` message directly as the commit message
7. **Commit staged changes** using `git commit -m` with YOUR drafted message
8. **Verify the commit** was successful
9. **Display the commit message** you created

## Argument Parsing

### --why Flag (Optional Context)

When `--why "message"` is provided in `$ARGUMENTS`:
- Extract the quoted message as additional context about the intent/reasoning behind the change
- This is NOT the commit message itself, but context to help you understand WHY the change was made
- Use this context along with the diff analysis to write a better commit message
- The message explains intent that may not be obvious from the code changes alone

### Parsing Examples

- `--all --why "fixing performance issue reported by users"` → Stage all changes, use context about performance
- `--why "refactoring to prepare for new feature"` → Use context about preparation purpose
- `--all` → Stage all changes, no additional context (use existing behavior)
- (no arguments) → Use existing behavior with staged changes only

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
