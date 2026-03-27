---
name: skill-authoring
description: Use when creating or modifying SKILL.md files
---

# Skill Authoring

This skill documents our conventions, not exhaustive OpenCode capabilities. Omissions are
intentional.

## What Skills Are

Skills are on-demand context modules that agents load via progressive disclosure. They provide
procedural knowledge (workflows, patterns, reference) without bloating always-loaded context.

**Skills are**: Reusable procedures, patterns, reference guides, tool documentation.

**Skills are NOT**: Invariants, constraints, or conventions that apply every session (those belong
in AGENTS.md).

## When to Create a Skill vs. AGENTS.md

**Litmus test**: Would you want this instruction to apply even when you're not thinking about it?
Yes = AGENTS.md (rules, constraints, conventions). No = skill (procedures, reference, workflows).

AGENTS.md can route to skills: `- testing: Use for any test-related work`. This keeps always-on
context small while making the agent adaptable.

Examples:

- "Never commit `.env` files" -> **AGENTS.md** (invariant)
- "When writing tests, follow these NUnit patterns" -> **Skill** (procedure)
- "Use `const` by default, `let` when reassignment needed" -> **AGENTS.md** (convention)
- "When creating decision records, follow this template" -> **Skill** (infrequent workflow)

## Progressive Disclosure

Skills load in three layers:

1. **Metadata** (~100 tokens): Name and description at startup. Agent uses this to decide relevance.
2. **SKILL.md body** (on trigger): Core instructions, patterns, workflows.
3. **Referenced files** (on demand): Heavy reference material the agent reads selectively.

Implications: the description determines whether the agent ever reads the body. Split into SKILL.md
plus referenced files only when the reference is genuinely separable (e.g., a 600-line API spec). If
the agent needs content every load, it belongs in SKILL.md.

## File Location and Discovery

- **Project-local**: `.opencode/skills/<name>/SKILL.md` (walks up to git worktree root)
- **Global**: `~/.config/opencode/skills/<name>/SKILL.md`

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

The description is the routing mechanism. Describe **when to use**, not what the skill contains.

Internal testing showed that descriptions summarizing the workflow cause the agent to follow the
description as a shortcut, skipping the full body.

```yaml
# BAD: Summarizes content (agent may shortcut)
description: Testing patterns, infrastructure, and fixtures for Recyclarr

# BAD: Too vague
description: For async testing

# GOOD: Triggering conditions only
description: Use when writing or modifying tests, improving coverage, or debugging test failures
```

Start with "Use when...", include specific situations and file paths, write in third person. NEVER
summarize the skill's process or workflow.

### Body Content

Open with a brief purpose statement, then actionable content. Every skill should address (not
necessarily as separate sections): what info it needs before starting, what the procedure is, how to
verify it worked, when to pause and ask the human, and what to do if a check fails.

## Content Balance

Include what the agent needs to act correctly, written concisely. The goal: zero wasted tool calls
for discovery without padding with verbose explanations.

**Guiding principle:** If the agent needs it every load, put it in SKILL.md. If only for specific
sub-tasks, put it in a referenced file.

- Cross-reference other skills by name instead of duplicating shared content
- One excellent example beats three mediocre ones
- Compress examples: minimal setups, no verbose scaffolding
- Terse rules and compressed prose; every sentence earns its place

### Directory Structures

Most skills are self-contained (`skill-name/SKILL.md`). Add subdirectories only when justified:

```txt
skill-name/
  SKILL.md              # Core workflows + always-needed reference
  references/           # Large docs the agent reads selectively
    api-reference.md
  scripts/              # Deterministic operations better as code
    validate.py
```

Reference from SKILL.md: "See `references/api-reference.md` for complete API documentation."

## Failure Modes

- **The Everything Bagel**: skill applies to every task. Fix: it's a rule, move it to AGENTS.md.
- **The Secret Handshake**: agent never loads the skill. Fix: description is too abstract, rewrite
  the trigger.
- **The Fragile Skill**: breaks when the repo changes. Fix: move specifics to referenced files.
- **The Shortcut**: agent follows the description and skips the body. Fix: remove workflow summary
  from the description.
- **The Skeleton**: agent wastes tool calls on discovery. Fix: include the needed reference material
  inline.
- **The Echo**: opener restates the trigger condition. Fix: state purpose, not loading instructions.

## Validation Checklist

- [ ] Frontmatter has required `name` and `description` fields
- [ ] Name matches directory name exactly
- [ ] Name follows naming rules (lowercase, hyphens only)
- [ ] Name is unique across all discovery locations
- [ ] `SKILL.md` filename is uppercase
- [ ] Description starts with "Use when" and states triggering conditions only
- [ ] Description does NOT summarize the skill's workflow or content
- [ ] Body starts with clear purpose statement
- [ ] Examples are copy-pasteable without modification
- [ ] Agent can act without discovery tool calls (needed references are inline)
- [ ] Content is concise; no filler prose or redundant explanations
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
