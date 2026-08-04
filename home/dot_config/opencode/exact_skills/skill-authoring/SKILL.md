---
name: skill-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing SKILL.md files and skill directories.
  Triggers on any edit to a SKILL.md file or skill directory (including chezmoi source forms).
  Do NOT use for AGENTS.md, agent definitions, or slash commands.
---

# Skill Authoring

Skills are on-demand procedures. AGENTS.md holds durable invariants; documentation holds reference
material; permissions and checks enforce deterministic rules.

## Decide whether to create a skill

Delete content that is inferable, duplicated, obsolete, or too generic to change behavior. Create a
skill only when a recurring task needs instructions that should not load for unrelated work.
Existing data files do not prove that their authoring workflow is still active. Check current use
and deletion history before creating or restoring a skill.

Use three layers:

1. `name` and `description`: metadata shown in the skill tool.
2. `SKILL.md`: the procedure needed whenever the skill is loaded.
3. Referenced files or scripts: optional detail loaded or executed only when required.

Do not move broad advice into AGENTS.md merely to shorten a skill. Keep a universal rule only when a
concrete failure justifies always loading it.

## Location and frontmatter

OpenCode discovers project skills under `.opencode/skills/<name>/SKILL.md` and global skills under
`~/.config/opencode/skills/<name>/SKILL.md`. It also supports compatible `.claude/skills` and
`.agents/skills` locations.

```yaml
---
name: skill-name
description: Use when creating or reviewing the artifact this skill governs.
---
```

- `name` is 1-64 lowercase alphanumeric characters separated by single hyphens and matches the
  directory name.
- `description` is 1-1024 characters.
- OpenCode also recognizes `license`, `compatibility`, and string-to-string `metadata`.
- Unknown frontmatter fields are ignored; do not invent behavioral fields.

## Write the description

The description is visible before the body loads. Describe triggers and boundaries, not the
procedure itself.

- Start with `Use when` as the local convention.
- Include common user phrasing, governed paths or tools, and adjacent terms when useful.
- Add a negative trigger only when a neighboring skill has an ambiguous boundary.
- Prefer a precise short description over an exhaustive keyword list.

Register the skill in always-loaded instructions only when missed loading repeatedly causes a
consequential error. Put primary-only registration in the primary prompt.

## Write the body

State the purpose, required inputs, procedure, failure behavior, and verification that the agent
cannot infer elsewhere. For CLI tools, teach sequencing and non-obvious semantics; defer ordinary
syntax to `--help`.

- Cross-reference another skill instead of copying it.
- Keep facts needed on every invocation in SKILL.md.
- Move large, separable reference material into `references/`.
- Use a script when deterministic transformation or validation is safer than prose.
- Include one example only when it communicates a contract more clearly than rules.
- Examples, including disposable checks, must obey the repository rules they are meant to teach.

The loaded skill must let the agent understand its workflow without broad preliminary discovery.
Repository discovery that is part of the workflow remains valid.

Before removing a schema, data shape, or procedure, inspect what the skill's consumers may read.
Keep the minimal canonical contract in the skill when permissions or workflow boundaries prevent
consumers from retrieving it elsewhere.

## Review

- Verify frontmatter against the current OpenCode documentation.
- Confirm the name matches the directory and is unique across discovery locations.
- Remove instructions inherited from AGENTS.md or another skill.
- Confirm permitted consumers can retrieve every contract removed from the skill body.
- Check that every rule prevents a current failure and every referenced path exists.
- Delete unused references and scripts rather than preserving an empty structure.
