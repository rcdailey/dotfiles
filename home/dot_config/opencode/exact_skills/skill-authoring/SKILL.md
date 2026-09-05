---
name: skill-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing SKILL.md or a skill directory, including
  chezmoi source forms. Do not use for AGENTS.md, agent definitions, or commands.
---

# Skill Authoring

Skills are on-demand procedures. Put durable invariants in AGENTS.md, reference material in docs,
and deterministic rules in permissions or checks.

Apply the active Authoring policy; this skill governs on-demand procedure discovery and packaging.

## Decide whether to create a skill

Create a skill only for a recurring procedure that should not load for unrelated work. Delete
inferable, duplicated, obsolete, and generic content. Existing files do not prove the workflow is
active; inspect current use and deletion history before restoring one.

Keep selection metadata in frontmatter, every-invocation procedure in SKILL.md, and optional detail
in referenced files or scripts. Put a universal rule in AGENTS.md only when a concrete failure
justifies loading it every session.

## Location and frontmatter

OpenCode discovers project skills under `.opencode/skills/<name>/SKILL.md` and global skills under
`~/.config/opencode/skills/<name>/SKILL.md`; compatible `.claude/skills` and `.agents/skills`
locations also work.

```yaml
---
name: skill-name
description: Use when creating or reviewing the artifact this skill governs.
---
```

- `name`: required, 1-64 lowercase alphanumeric characters separated by single hyphens; matches its
  directory.
- `description`: required, 1-1024 characters.
- `license`, `compatibility`, and string-to-string `metadata`: optional.
- Unknown fields are ignored; do not invent behavioral fields.

## Write the description

The description selects the skill before its body loads. Describe triggers and boundaries, not the
procedure.

- Start with `Use when` as the local convention.
- Include likely user phrasing, governed paths, and tool names when useful.
- Add a negative trigger only when a neighboring skill has an ambiguous boundary.
- Prefer precision over an exhaustive keyword list.

Register the skill in always-loaded instructions only when missed loading repeatedly causes a
consequential error. Put primary-only registration in the primary prompt.

## Write the body

Include only purpose, inputs, procedure, failure behavior, and verification the agent cannot infer.
For CLI tools, teach sequencing and non-obvious semantics; defer syntax to `--help`.

- Cross-reference another skill instead of copying it.
- Move large, separable reference material into `references/`.
- Use a script when deterministic transformation or validation is safer than prose.
- Include one example only when it communicates a contract better than rules.
- Require examples and disposable checks to obey the rules they teach.

The loaded skill must support action without broad preliminary discovery; task-specific repository
discovery remains valid.

Before removing a contract, inspect what consumers can read. Keep its minimal canonical form in the
skill when permissions or workflow prevent retrieval elsewhere.

## Review

- Verify frontmatter against the current OpenCode documentation.
- Confirm the name matches its directory and is unique across discovery locations.
- Remove instructions inherited from AGENTS.md or another skill.
- Confirm consumers can retrieve every contract removed from the body.
- Require every rule to prevent a current failure and every referenced path to exist.
- Delete unused references and scripts rather than preserving an empty structure.
