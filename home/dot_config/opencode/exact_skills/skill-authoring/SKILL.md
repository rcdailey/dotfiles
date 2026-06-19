---
name: skill-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing SKILL.md files and skill directories.
  Triggers on any edit to a SKILL.md file or skill directory (including chezmoi source forms).
  Do NOT use for AGENTS.md, agent definitions, or slash commands.
---

# Skill Authoring

Conventions for SKILL.md files. Omissions intentional. All authored content MUST follow the
Authoring rules in global AGENTS.md.

## Skills vs. AGENTS.md

Skills are on-demand context modules loaded via progressive disclosure; they hold procedural
knowledge (workflows, patterns, reference). AGENTS.md holds invariants, constraints, and conventions
that apply every session.

Litmus test: would this apply even when you're not thinking about it? Yes = AGENTS.md. No = skill.

Examples: "Never commit `.env` files" -> AGENTS.md (invariant). "When creating decision records,
follow this template" -> skill (infrequent workflow).

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

The description is the ONLY signal for loading. Body content is not consulted at selection time.
Bias toward pushy descriptions: missed invocations are silent; over-triggers are visible and
correctable. Describe triggers, not workflow (avoids The Shortcut failure mode).

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

Frontmatter alone triggers roughly half as often as skills with reinforcing AGENTS.md directives.

- Every skill MUST be registered in `AGENTS.md` or `opencode-primary-shared.md` (primary-only scope)
  with an imperative RFC 2119 trigger.
- Primary-only skills MUST live in the primary-shared partial to avoid subagent context bloat.
- For deterministic workflows, `disable-model-invocation: true` forces explicit `/skill-name`
  invocation.

## Body Content

Open with purpose, then actionable content. Cover: inputs, procedure, verification, when to ask the
human, failure handling.

- If the agent needs it every load, put it in SKILL.md; otherwise, referenced file.
- Cross-reference other skills by name instead of duplicating.
- See `agents-authoring` for RFC 2119 rule writing conventions.
- **CLI tool skills**: teach workflow and semantics; defer to `--help` for syntax. Cover what the
  tool cannot self-document: sequencing, failure handling, non-obvious interactions.

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

- **Ghost** (undertriggering): too narrow. Fix: more phrasings, extensions, synonyms.
- **Orphan**: no AGENTS.md reinforcement. Fix: register with RFC 2119 trigger.
- **Shortcut**: description summarizes workflow; model skips body. Fix: triggers only.
- **Everything Bagel**: applies every task. Fix: move to AGENTS.md.
- **Fragile**: breaks when repo changes. Fix: move specifics to referenced files.
- **Skeleton**: agent wastes tool calls on discovery. Fix: inline reference material.
- **Echo**: body opener restates trigger. Fix: state purpose instead.
- **Reserved Name**: starts with `claude`/`anthropic`. Fix: rename.
- **Imposter**: `README.md` instead of `SKILL.md`. Fix: rename.
- **Escape**: raw `<`/`>` in frontmatter. Fix: rephrase.

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
- [ ] Any examples present are copy-pasteable without modification
- [ ] Agent can act without excessive discovery tool calls (one `--help` is acceptable)
