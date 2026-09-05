---
name: agents-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing AGENTS.md or global directives, including
  chezmoi source forms. Do not use for skills, agent definitions, or commands.
---

# AGENTS.md Authoring

AGENTS.md contains only non-obvious, durable rules for its effective scope. It is not a repository
manual.

Apply the active Authoring policy; this skill governs rule placement and loading.

## Decide what belongs

Apply this order to every candidate instruction:

1. Delete it if code, tool help, configuration, or ordinary conventions already reveal it.
2. Enforce it with permissions, tests, schemas, hooks, or linters when deterministic.
3. Put task-specific procedures in a skill and detailed reference material in documentation.
4. Keep it in AGENTS.md only when it is durable, consequential, and broadly applicable.

Keep unusual commands, architectural boundaries, operational hazards, and a small map to
authoritative files only when they prevent a known failure.

## Scope and loading

OpenCode loads global AGENTS.md and the first project rule file found above the working directory.
Its read tool also injects applicable child AGENTS.md files above a target file; shell reads do not.

For package-specific guidance, choose one of these deliberately:

- A local AGENTS.md when rules apply to files in that subtree and normal work reads those files.
- The `instructions` setting when package rules must load before any file read.
- A root pointer when a workflow may act through tools that do not trigger contextual loading.

Keep one authoritative location per rule; lower scopes reference higher scopes.

## Write rules

- State the required behavior and the condition that triggers it.
- Use `MUST` or `MUST NOT` only for hard requirements.
- Replace vague qualities with an observable result or a real example path.
- Give the valid alternative when prohibiting an action.
- Omit prose that only restates structural enforcement.
- Scope primary-only delegation rules explicitly; every agent receives global AGENTS.md.
- Register a skill in always-loaded instructions only after repeated consequential misses.
- Put primary-only skill registration in the primary prompt, not global context.

## Review

- Verify every path and command against the repository.
- Inspect history before restoring a removed instruction or workflow; absence may be intentional.
- Remove duplicated, stale, generic, speculative, and inferable guidance.
- Confirm each remaining rule has one authoritative home and a concrete failure it prevents.
- Keep only enough repository structure to direct the next read.
