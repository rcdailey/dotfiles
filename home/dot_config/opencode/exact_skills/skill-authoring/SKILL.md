---
name: skill-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing SKILL.md files and skill directories.
  Triggers on any edit to a SKILL.md file or skill directory (including chezmoi source forms).
  Do NOT use for AGENTS.md, agent definitions, or slash commands.
---

# Skill Authoring

Conventions for SKILL.md files. Omissions intentional.

## Skills vs. AGENTS.md

Skills are on-demand context modules loaded via progressive disclosure; they hold procedural
knowledge (workflows, patterns, reference). AGENTS.md holds invariants, constraints, and conventions
that apply every session.

Litmus test: would this apply even when you're not thinking about it? Yes = AGENTS.md. No = skill.

Examples:

- "Never commit `.env` files" -> AGENTS.md (invariant)
- "When writing tests, follow these NUnit patterns" -> skill (procedure)
- "Use `const` by default" -> AGENTS.md (convention)
- "When creating decision records, follow this template" -> skill (infrequent workflow)

## Progressive Disclosure

Three layers:

1. **Metadata** (~100 tokens): `name` + `description` in always-loaded context. Decides relevance.
2. **SKILL.md body** (on trigger): core instructions.
3. **Referenced files** (on demand): heavy reference material read selectively.

The description decides whether the body is ever read. If the agent needs content every load, it
belongs in SKILL.md. Split into referenced files only when genuinely separable (e.g., a 600-line API
spec).

## File Location

- Project: `.opencode/skills/<name>/SKILL.md` (walks up to git worktree root)
- Global: `~/.config/opencode/skills/<name>/SKILL.md`

Skill name MUST match directory name.

## Frontmatter

```yaml
---
name: skill-name
description: Use when [triggering conditions]
---
```

- `name`: 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing/consecutive hyphens
- `description`: 1-1024 chars (under 500 preferred)

## Description: The Sole Selection Signal

The description is the ONLY signal that decides loading. File name, directory structure, and body
content are not consulted at selection time. A great body is useless if the description does not
trigger.

**Bias toward pushy, comprehensive descriptions.** The model undertriggers by default. Missed
invocations are silent; over-triggers surface as visible misfires the user can correct. When in
doubt, add more triggers.

**Describe triggers, not workflow.** Descriptions summarizing capabilities cause the model to treat
the description as a shortcut and skip the body (The Shortcut failure mode). Capability lists and
"this skill does X" phrasing belong in the body, never the description.

Required trigger coverage:

- Opens with `Use when`
- Multiple phrasings users actually type (synonyms, abbreviations, casual and formal forms)
- File extensions, paths, or tool names the skill governs (`.cs`, `SKILL.md`, `gh-review`)
- Adjacent terms that should route here (framework names, feature names)
- Negative triggers (`Do NOT use for X`) when sibling-skill boundaries are fuzzy
- Under 1024 chars; under 500 preferred
- No `<` or `>` characters (parsed as XML/HTML tokens and rejected)

Trigger coverage beats brevity; trim body prose before trigger phrases.

Examples:

```yaml
# BAD: too narrow, single phrasing
description: Use when writing C# code

# BAD: summarizes workflow (shortcut risk)
description: Testing patterns, infrastructure, and fixtures for Recyclarr

# GOOD: multiple phrasings, extensions, alternate terms, negative trigger
description: >-
  Use when writing, editing, reviewing, or refactoring C# code or .NET projects
  (`.cs`, `.csproj`, `.razor`, `.cshtml`); working on dotnet, ASP.NET, Blazor, MAUI,
  EF Core, or Roslyn tasks; applying modern C# features, nullable reference types, or
  async patterns. Do NOT use for F#, VB.NET, or non-CLR languages.
```

## Triggering Reliability

Description tuning alone is insufficient for consistent invocation. Empirical testing shows skills
relying on frontmatter alone trigger roughly half as often as skills with reinforcing AGENTS.md
directives. Past a minimum clarity bar, adding description length yields diminishing returns;
specificity of trigger phrases beats verbosity.

- Every skill MUST be registered in `AGENTS.md` (all agents) or `opencode-primary-shared.md`
  (primary-only scope) with an imperative trigger using RFC 2119 keywords.
- Primary-only skills (GitHub publishing, PR review) MUST live in the primary-shared partial to
  avoid subagent context bloat.
- For deterministic workflows (commit, deploy), `disable-model-invocation: true` in frontmatter
  eliminates undertriggering by forcing explicit `/skill-name` invocation.

## Body Content

Open with a brief purpose statement, then actionable content. Address (not necessarily as separate
sections): inputs needed before starting, the procedure, verification, when to pause and ask the
human, what to do if a check fails.

Guiding principle: if the agent needs it every load, put it in SKILL.md; otherwise, referenced file.
Cross-reference other skills by name instead of duplicating. One excellent example beats three
mediocre ones. Compress examples to minimal setups. See `agents-authoring` for RFC 2119 rule writing
conventions.

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

- **The Ghost** (undertriggering): description too narrow or single-phrased. Fix: expand trigger
  coverage; add phrasings, extensions, synonyms.
- **The Orphan**: description is solid but no reinforcing directive in AGENTS.md or primary-shared,
  so invocation is inconsistent. Fix: register the skill at the correct scope with an RFC 2119
  imperative trigger.
- **The Shortcut**: description summarizes workflow; model skips loading the body. Fix: strip the
  summary; state only when to load.
- **The Everything Bagel**: applies to every task (it's a rule, not a procedure). Fix: move to
  AGENTS.md.
- **The Fragile Skill**: breaks when the repo changes. Fix: move specifics to referenced files.
- **The Skeleton**: agent wastes tool calls on discovery during execution. Fix: inline the reference
  material.
- **The Echo**: body opener restates the trigger. Fix: state purpose, not loading instructions.
- **The Reserved Name**: name starts with `claude` or `anthropic` (reserved). Fix: rename.
- **The Imposter**: `README.md` in the skill directory; OpenCode loads `SKILL.md` only. Fix: rename
  or remove.
- **The Escape**: raw `<` or `>` in frontmatter `description`. Fix: rephrase.

## Validation Checklist

- [ ] Frontmatter has `name` and `description`
- [ ] Name matches directory; lowercase alphanumeric + hyphens; 1-64 chars
- [ ] Name does not start with `claude` or `anthropic`
- [ ] Name unique across discovery locations
- [ ] `SKILL.md` filename uppercase; no `README.md` sibling
- [ ] No `<` or `>` anywhere in frontmatter values
- [ ] Description opens with `Use when`
- [ ] Description states triggers only; no workflow summary
- [ ] Description includes multiple phrasings, relevant extensions/paths/tools
- [ ] Description includes negative triggers when sibling boundary is fuzzy
- [ ] Description under 1024 chars (under 500 preferred)
- [ ] Skill registered in `AGENTS.md` or `opencode-primary-shared.md` with RFC 2119 trigger
- [ ] Registration scoped correctly (primary-only skills in primary-shared)
- [ ] Body opens with purpose statement (not a restated trigger)
- [ ] Examples copy-pasteable without modification
- [ ] Agent can act without discovery tool calls
