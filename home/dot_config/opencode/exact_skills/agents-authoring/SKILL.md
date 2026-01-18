---
name: agents-authoring
description: Best practices for writing AGENTS.md and skill files based on research from GitHub, Anthropic, and industry patterns
---

# AGENTS.md and Skill Authoring

Load this skill when creating or updating AGENTS.md files or OpenCode skills.

## Research Foundation

This guidance is based on:

- GitHub's analysis of 2,500+ repositories with agents.md files
- Anthropic's context engineering documentation
- OpenAI Codex custom instructions guide
- Devin AI's good vs bad instructions documentation

## Six Core Areas (GitHub Research)

Effective agent instructions cover these areas:

| Area                 | Purpose                    | Example                           |
|----------------------|----------------------------|-----------------------------------|
| Commands First       | Executable strings early   | `npm test`, `make build`          |
| Real Code Examples   | Snippets over descriptions | Show actual patterns, not prose   |
| Hard Boundaries      | What agent must never do   | "NEVER commit secrets"            |
| Tech Stack Specifics | Precise about technologies | "Python 3.12 with FastAPI"        |
| Project Structure    | Where agent reads/writes   | Directory patterns, file purposes |
| Testing/Verification | How agent verifies work    | Commands to validate changes      |

## Anthropic Context Engineering Principles

### Clarity at the Right Altitude

- Specific enough to guide behavior effectively
- Flexible enough to provide strong heuristics
- Not so detailed it becomes brittle

### Minimality

- Minimal set of information that fully outlines expected behavior
- Minimal does NOT mean short - it means only necessary information
- Remove redundancy ruthlessly

### Structure

- Organize into distinct sections
- Group related rules together
- Use consistent formatting

## Token Efficiency Patterns

### Do

- Use `path:line` pointers over large code pastes
- Reference existing files as templates ("see src/api/users.ts for pattern")
- Point to `--help` for script usage instead of embedding examples
- Use retrieval on-demand (skills) vs pre-loading everything
- Consolidate related rules into single locations

### Don't

- Repeat the same rule in multiple sections
- Embed large code examples that could be referenced
- Include queryable/discoverable information (API docs, man pages)
- Pre-load information needed only for specific operations

## Rule Writing Guidelines

### Format: Constraint + Consequence

Bad: "Don't commit directly to main"

Good: "NEVER commit directly to main - use feature branches and PRs for review"

### Prefer Positive Over Negative

When possible, say what TO do, not just what NOT to do:

Bad: "NEVER use var in JavaScript"

Good: "Use `const` by default, `let` when reassignment needed (NEVER `var`)"

### Be Specific, Not Vague

Bad: "Be careful with error handling"

Good: "All async functions MUST have try/catch - unhandled rejections crash the process"

### Use Examples Over Adjectives

Bad: "Write concise, professional commit messages"

Good: "Examples: `fix(auth): handle expired tokens`, `feat(api): add user search endpoint`"

## Antipatterns to Avoid

| Antipattern                       | Problem                       | Fix                            |
|-----------------------------------|-------------------------------|--------------------------------|
| Verbose explanations              | Wastes tokens                 | Terse rule + consequence       |
| Repeated rules                    | Inconsistency risk            | Single authoritative location  |
| Vague adjectives                  | Subjective interpretation     | Concrete criteria or examples  |
| Embedded discoverable info        | Stale, bloated                | Point to source (--help, docs) |
| Prohibitions without alternatives | Agent doesn't know what TO do | Include the correct approach   |
| Over-engineered modes/workflows   | Complexity without benefit    | Simple, direct instructions    |

## AGENTS.md Structure Template

```markdown
# Project Name

Brief description. Repository location.

## Reference Sources

Links to authoritative patterns, documentation, reference implementations.

## Constraints

Hard boundaries grouped by domain. Format: rule + consequence.

### Domain 1 (e.g., Code Quality)

- NEVER/MUST rules with consequences

### Domain 2 (e.g., Security)

- NEVER/MUST rules with consequences

## Commands

Executable commands early in file. Terse, copy-pasteable.

## Project Structure

Directory patterns, file purposes. Pattern-based, not exhaustive lists.

## Conventions

Naming, formatting, style guidelines. Consolidated, not scattered.

## Environment

Infrastructure facts that don't change often (versions, services, endpoints).

## Skills

Pointers to on-demand skills for detailed patterns.

## Commits

Commit message format, type selection guidance.
```

## Skill Structure (OpenCode)

### Location

- Project: `.opencode/skill/{name}/SKILL.md`
- Global: `~/.config/opencode/skill/{name}/SKILL.md`

### Frontmatter (Required)

```yaml
---
name: skill-name
description: 1-1024 chars describing when to use this skill
---
```

### Name Rules

- 1-64 characters
- Lowercase alphanumeric with single hyphen separators
- No leading/trailing hyphens
- No consecutive hyphens
- Must match directory name

### Body Content

- Start with "Load this skill when..." guidance
- Include complete, copy-pasteable examples
- Show pattern variations
- Include checklists for complex operations
- Document common mistakes

## When to Use Skills vs AGENTS.md

### Put in AGENTS.md (always loaded)

- Critical constraints that prevent breakage
- Commands needed in most conversations
- Project structure patterns
- Environment/infrastructure facts
- Pointers to skills

### Put in Skills (loaded on demand)

- Detailed file templates
- Step-by-step procedures
- Pattern variations
- Domain-specific knowledge
- Comprehensive examples

### Decision Heuristic

Ask: "Is this needed in every conversation?"

- Yes -> AGENTS.md
- No, only for specific operations -> Skill

## Good vs Bad Instructions (Devin Research)

### Good Instructions

- Name specific files/components
- Reference existing code as templates
- Include clear success criteria
- Define verification steps
- Specify data sources

Example: "Create endpoint `/users/stats` returning JSON with user count. Reference `/orders/stats`
in `statsController.js` for response structure. Add tests to `StatsController.test.js`."

### Bad Instructions

- Vague ("make it user-friendly")
- No specific components mentioned
- Unclear validation criteria
- Open-ended scope
- Missing context

Example: "Add a user stats endpoint." (No format, source, tests, or reference)

## Maintenance Guidelines

### When to Update AGENTS.md

- New hard constraints discovered
- Infrastructure/environment changes
- Command changes
- Structure changes

### When to Update Skills

- New patterns established
- Existing patterns proven outdated
- Common mistakes discovered
- Better examples found

### Update Process

1. Identify what changed and why
2. Update the authoritative location (not duplicates)
3. Verify no contradictions introduced
4. Run markdownlint to validate formatting
5. Commit with clear description of what changed

## Validation Checklist

Before finalizing AGENTS.md or skill changes:

- [ ] No duplicate rules across sections
- [ ] Each constraint has a consequence
- [ ] Commands are copy-pasteable
- [ ] Examples are from actual codebase (not invented)
- [ ] Skills are referenced where detailed patterns live
- [ ] Line length <= 100 characters
- [ ] No duplicate headings
- [ ] Code blocks have language specifiers
- [ ] Passes markdownlint
