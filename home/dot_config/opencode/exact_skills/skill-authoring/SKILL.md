---
name: skill-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing SKILL.md files and skill directories;
  writing or revising skill frontmatter (`name`, `description`) for reliable triggering;
  diagnosing undertriggering or shortcut failure modes; splitting skill content between
  SKILL.md and referenced files; auditing a skill for scope, progressive disclosure, or
  redundancy. Triggers on any edit to a SKILL.md file or skill directory (including chezmoi
  source forms).
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

### Description: The Sole Selection Signal

The description is the ONLY signal that decides whether the agent loads the skill. File name,
directory structure, and body content are not consulted at selection time; only `name` and
`description` sit in always-loaded context. A great body is useless if the description does not
trigger.

**Bias toward pushy, comprehensive descriptions.** The model undertriggers skills by default
(documented by Anthropic; observed locally). Missed invocations are silent (the user must notice the
skill was skipped); over-triggers surface as visible misfires the user can correct. When in doubt,
add more triggers.

**Describe triggers, not workflow.** Local testing showed descriptions that summarize capabilities
or workflow cause the model to treat the description as a shortcut and skip the body (`The Shortcut`
failure mode). Anthropic's public skill examples mix "what it does" with "when to use"; our
convention is triggers-only because the shortcut cost outweighs the discoverability gain. Capability
lists, procedure outlines, and "this skill does X" phrasing belong in the body, never the
description.

**Required trigger coverage:**

- Opens with `Use when`
- Names multiple phrasings users actually type (synonyms, abbreviations, casual and formal forms)
- Names file extensions, paths, or tool names the skill governs (`.cs`, `SKILL.md`, `gh-review`,
  `.opencode/commands/`)
- Names adjacent terms that should route here (framework names, feature names, related file types)
- Includes negative triggers (`Do NOT use for X`) when the boundary with an adjacent skill is fuzzy
- Stays under 1024 chars (hard limit); under 500 preferred when trigger coverage allows
- No `<` or `>` characters (parsed as XML/HTML tokens and rejected)

**Size discipline:** trigger coverage beats brevity. Do not trim trigger phrases to shrink the
description; trim body prose instead.

Examples:

```yaml
# BAD: too narrow, single phrasing, no alternate terms or extensions
description: Use when writing C# code

# BAD: summarizes workflow (shortcut risk)
description: Testing patterns, infrastructure, and fixtures for Recyclarr

# BAD: passive phrasing, no triggers
description: For async testing

# BAD: content summary with no "Use when"
description: Conventions and patterns for OpenCode custom commands

# GOOD: multiple phrasings, file extensions, alternate terms, negative trigger
description: >-
  Use when writing, editing, reviewing, or refactoring C# code or .NET projects
  (`.cs`, `.csproj`, `.razor`, `.cshtml`); working on dotnet, ASP.NET, Blazor, MAUI,
  EF Core, or Roslyn tasks; applying modern C# features, nullable reference types, or
  async patterns. Do NOT use for F#, VB.NET, or non-CLR languages.
```

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

- **The Ghost Skill** (undertriggering): agent never loads the skill even when the task clearly
  matches. Cause: description too narrow, single phrasing, missing file extensions or alternate
  terms. Fix: expand trigger coverage per the Description section; add phrasings, extensions, and
  synonyms users actually type.
- **The Shortcut**: agent reads the description, treats it as a content summary, and skips loading
  the body. Cause: description summarizes workflow or capabilities instead of triggers. Fix: strip
  the summary; state only when to load.
- **The Everything Bagel**: skill applies to every task. Cause: it's actually a rule, not a
  procedure. Fix: move to AGENTS.md.
- **The Fragile Skill**: breaks when the repo changes. Fix: move specifics to referenced files; keep
  general procedure in SKILL.md.
- **The Skeleton**: agent wastes tool calls on discovery during execution. Fix: inline the reference
  material the agent needs on every load.
- **The Echo**: body opener restates the trigger condition. Fix: state purpose, not loading
  instructions.
- **The Reserved Name**: name starts with `claude` or `anthropic` (reserved by Anthropic). Fix:
  rename.
- **The Imposter**: a `README.md` inside the skill directory instead of (or alongside) `SKILL.md`.
  OpenCode loads `SKILL.md` only; `README.md` is ignored. Fix: rename or remove.
- **The Escape**: frontmatter `description` contains raw `<` or `>` characters, parsed as XML/HTML
  tokens and rejected. Fix: rephrase to avoid angle brackets.

## Validation Checklist

- [ ] Frontmatter has required `name` and `description` fields
- [ ] Name matches directory name exactly
- [ ] Name follows naming rules (lowercase alphanumeric + hyphens, 1-64 chars)
- [ ] Name does not start with `claude` or `anthropic` (reserved)
- [ ] Name is unique across all discovery locations
- [ ] `SKILL.md` filename is uppercase; no `README.md` sibling
- [ ] No `<` or `>` characters anywhere in frontmatter values
- [ ] Description opens with `Use when`
- [ ] Description states triggers only; no workflow summary or capability list
- [ ] Description includes multiple phrasings users might type for the same intent
- [ ] Description names relevant file extensions, paths, or tool names
- [ ] Description includes negative triggers when a sibling skill has a fuzzy boundary
- [ ] Description under 1024 chars (under 500 preferred)
- [ ] Body opens with a clear purpose statement (not a restated trigger)
- [ ] Examples are copy-pasteable without modification
- [ ] Agent can act without discovery tool calls (needed references inline)
- [ ] Content is concise; no filler prose or redundant explanations
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
