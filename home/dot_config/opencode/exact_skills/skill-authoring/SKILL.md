---
name: skill-authoring
description: Use when creating or modifying SKILL.md files
---

# Skill Authoring

## What Skills Are

Skills are on-demand context modules that agents load via progressive disclosure. They provide
procedural knowledge (workflows, patterns, reference) without bloating always-loaded context.

**Skills are**: Reusable procedures, patterns, reference guides, tool documentation.

**Skills are NOT**: Invariants, constraints, or conventions that apply every session (those belong
in AGENTS.md).

## When to Create a Skill vs. AGENTS.md

**Litmus test**: Would you want this instruction to apply even when you're not thinking about it?

- **Yes**: Put in AGENTS.md (rules, constraints, conventions, build commands)
- **No**: Put in a skill (procedures, reference, infrequent workflows)

AGENTS.md can serve as routing logic that points to skills:

```markdown
## Skills
- `testing` - Use for any test-related work
- `changelog` - Use when updating CHANGELOG.md
```

This keeps always-on context small while making the agent adaptable.

### Concrete examples

- "Never commit `.env` files" -> **AGENTS.md** (invariant)
- "When writing tests, follow these NUnit patterns" -> **Skill** (procedure)
- "Use `const` by default, `let` when reassignment needed" -> **AGENTS.md** (convention)
- "When creating decision records, follow this template" -> **Skill** (infrequent workflow)
- "When touching billing code, run these integration tests" -> **Skill** (conditional procedure)

## Progressive Disclosure

Skills use a three-layer loading model to manage context efficiently:

1. **Metadata** (~100 tokens): Name and description loaded at startup for all installed skills. The
   agent uses this to decide relevance.
2. **SKILL.md body** (loaded when triggered): Core instructions, patterns, and workflows.
3. **Referenced files** (loaded on demand): Heavy reference material, scripts, and templates that
   the agent reads only when needed.

This means a project can have dozens of skills installed with minimal context cost. Only the 2-3
relevant skills get fully loaded per session.

### Implications for authoring

- Keep SKILL.md lean; link out for heavy content (100+ lines of reference)
- The description determines whether the agent ever reads the body
- Referenced files (scripts/, references/) provide unbounded depth without upfront cost

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
description: Use when [triggering conditions]
---
```

- `name`: 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing/consecutive hyphens
- `description`: 1-1024 chars (under 500 preferred)

### Description: The Most Critical Field

The description determines when the agent loads the skill. It is the **routing mechanism**.

**CRITICAL**: Describe **when to use**, not **what the skill contains or does**.

obra/superpowers testing revealed that descriptions summarizing the skill's workflow cause the agent
to follow the description as a shortcut instead of reading the full SKILL.md body. The skill body
becomes documentation the agent skips.

```yaml
# BAD: Summarizes content (agent may shortcut)
description: Testing patterns, infrastructure, and fixtures for Recyclarr

# BAD: Describes what it does
description: Creates consistent releases and changelogs

# BAD: Too vague
description: For async testing

# GOOD: Triggering conditions only
description: Use when writing or modifying tests, improving coverage, or debugging test failures

# GOOD: Specific triggers
description: Use when creating or editing ADRs or PDRs in docs/decisions/

# GOOD: Technology-scoped trigger
description: Use when writing or modifying C# code
```

**Guidelines:**

- Start with "Use when..." to focus on triggering conditions
- Include specific symptoms, situations, and file paths that signal relevance
- Write in third person (injected into system prompt)
- NEVER summarize the skill's process or workflow

### Body Content

Open with a brief purpose statement, then provide actionable content.

**Recommended structure:**

```markdown
# Skill Name

## Overview (optional)
Core concept in 1-2 sentences. When NOT to use.

## [Core Content]
Patterns, procedures, commands, reference material.

## Common Mistakes
What goes wrong and how to fix it.
```

**Every skill should answer these questions** (not necessarily as sections):

1. **Trigger**: When should the agent load this? (covered by description)
2. **Inputs**: What info does it need before starting?
3. **Steps**: What is the procedure?
4. **Checks**: How to verify it worked?
5. **Stop conditions**: When to pause and ask the human?
6. **Recovery**: What if a check fails?

## Token Efficiency

Skills load into the context window. Every token counts, especially for frequently-triggered skills.

**Target sizes:**

- Frequently-triggered skills: under 200 words if possible
- Standard skills: under 500 words
- Reference-heavy skills: split into SKILL.md (lean) + referenced files (deep)

**Techniques:**

- Reference `--help` output instead of documenting all flags inline
- Cross-reference other skills by name instead of repeating their content
- One excellent example beats three mediocre ones
- Compress examples; avoid verbose setups when a minimal example suffices

**Splitting heavy content:**

```txt
my-skill/
  SKILL.md          # Overview + workflows (lean)
  references/
    api-reference.md  # 600 lines of API docs
    patterns.md       # Detailed code patterns
```

Reference from SKILL.md: "See `references/api-reference.md` for complete API documentation."

## Directory Structure

### Self-contained skill

```txt
skill-name/
  SKILL.md    # Everything inline
```

When: All content fits without exceeding ~500 words.

### Skill with reference material

```txt
skill-name/
  SKILL.md           # Overview + workflows
  references/
    detailed-ref.md  # Heavy reference docs
```

When: Reference material is too large for inline.

### Skill with scripts

```txt
skill-name/
  SKILL.md    # Overview + when to run scripts
  scripts/
    validate.py
```

When: Deterministic operations better handled by code than token generation.

## Failure Modes

| Failure              | Symptom                               | Fix                                        |
|----------------------|---------------------------------------|--------------------------------------------|
| The Encyclopedia     | SKILL.md reads like a wiki            | Split into lean body + referenced files    |
| The Everything Bagel | Skill applies to every task           | It's a rule, move to AGENTS.md             |
| The Secret Handshake | Agent never loads the skill           | Description too abstract; rewrite triggers |
| The Fragile Skill    | Breaks when repo changes              | Move specifics to referenced files         |
| The Shortcut         | Agent follows description, skips body | Remove workflow summary from description   |

## Validation Checklist

- [ ] Frontmatter has required `name` and `description` fields
- [ ] Name matches directory name exactly
- [ ] Name follows naming rules (lowercase, hyphens only)
- [ ] Description starts with "Use when" and states triggering conditions only
- [ ] Description does NOT summarize the skill's workflow or content
- [ ] Body starts with clear purpose statement
- [ ] Examples are copy-pasteable without modification
- [ ] Heavy reference material is in separate files, not inline
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
