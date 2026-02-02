---
name: skill-authoring
description: Best practices for creating and maintaining OpenCode SKILL.md files
---

# Skill Authoring

Load this skill when creating or modifying SKILL.md files.

## What Skills Are

Skills are specialized knowledge modules that agents load on demand. They provide detailed patterns,
examples, and procedures without bloating always-loaded agent context. Think of skills as reference
manuals agents consult when performing specific operations.

## File Location and Discovery

OpenCode searches these paths (first match wins):

**Project-local** (walks up to git worktree root):

- `.opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`

**Global**:

- `~/.config/opencode/skills/<name>/SKILL.md`
- `~/.claude/skills/<name>/SKILL.md`

The skill name MUST match the directory name.

## SKILL.md Structure

### Required Frontmatter

```yaml
---
name: skill-name
description: 1-1024 chars describing when to use this skill
---
```

### Optional Frontmatter

```yaml
---
name: git-release
description: Create consistent releases and changelogs
license: MIT
compatibility: opencode
metadata:
  audience: maintainers
  workflow: github
---
```

### Naming Rules

- 1-64 characters
- Lowercase alphanumeric only
- Single hyphens as separators (no consecutive hyphens)
- No leading or trailing hyphens
- Must match containing directory name

Valid: `git-release`, `csharp-coding`, `pr-review`
Invalid: `Git-Release`, `git--release`, `-git-release`, `git_release`

## Body Content Guidelines

### Start with Purpose

Open with a clear statement of what the skill covers and when to load it.

```markdown
# Git Release Skill

Load this skill when preparing tagged releases or drafting changelogs.
```

### Include Copy-Pasteable Examples

Examples should be ready to use without modification. Avoid placeholders that require editing.

````markdown
## Release Command

```bash
gh release create v1.2.3 --title "v1.2.3" --notes-file CHANGELOG.md
```
````

### Show Pattern Variations

Cover common variations rather than a single happy path.

````markdown
## Version Bump Patterns

Patch (bug fixes):
```bash
npm version patch
```

Minor (new features, backward compatible):
```bash
npm version minor
```

Major (breaking changes):
```bash
npm version major
```
````

### Document Common Mistakes

Prevent repeated errors by calling them out explicitly.

```markdown
## Common Mistakes

- Forgetting to push tags: `git push --tags`
- Creating release before merging PR (changelog references wrong commit)
- Using `v` prefix inconsistently (pick one: `v1.0.0` or `1.0.0`)
```

## Skill Permissions

Configure which skills agents can access in `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "pr-review": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}
```

Permission levels:

- **allow**: Agent can load immediately
- **deny**: Hidden from agent entirely
- **ask**: Requires user approval before loading

Patterns support wildcards (`*`) for matching multiple skills.

## Maintenance

Update skills when:

- New patterns emerge from usage
- Better examples are discovered
- Common mistakes are identified
- Tool versions change syntax

Process:

1. Identify what changed and why
2. Update examples to remain copy-pasteable
3. Verify no contradictions with agent prompts
4. Validate formatting (markdownlint)

## Validation Checklist

Before finalizing changes:

- [ ] Frontmatter has required `name` and `description` fields
- [ ] Name matches directory name exactly
- [ ] Name follows naming rules (lowercase, hyphens only)
- [ ] Description is 1-1024 characters
- [ ] Body starts with clear purpose statement
- [ ] Examples are copy-pasteable without modification
- [ ] Common mistakes documented
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
