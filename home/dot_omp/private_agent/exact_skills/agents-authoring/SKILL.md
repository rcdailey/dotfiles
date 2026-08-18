---
name: agents-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing AGENTS.md files at any level (repo,
  package, or global). Triggers on phrases like "update AGENTS.md", "add a rule to AGENTS.md",
  "global directives", or any edit to a file named AGENTS.md (including chezmoi source forms).
  Do NOT use for SKILL.md, agent definitions, or slash commands.
---

# AGENTS.md Authoring

Use AGENTS.md for concise, non-obvious rules that apply throughout its effective scope. It is not a
repository manual.

## Decide what belongs

Apply this order to every candidate instruction:

1. Delete it if code, tool help, configuration, or ordinary conventions already reveal it.
2. Enforce it with permissions, tests, schemas, hooks, or linters when deterministic.
3. Put task-specific procedures in a skill and detailed reference material in documentation.
4. Keep it in AGENTS.md only when it is durable, consequential, and broadly applicable.

Useful content often includes unusual commands, architectural boundaries, operational hazards, and a
small map to authoritative files. Include examples or escalation guidance only when they prevent a
known failure.

## Scope and loading

OMP loads user instructions from `~/.omp/agent/AGENTS.md`. It walks from the working directory to the
repository boundary for standalone project AGENTS.md files. A native `.omp/AGENTS.md` at the nearest
non-empty `.omp` directory wins over lower-priority conventions at the same depth.

OMP removes AGENTS.md context from task subagents. Put instructions needed by primary sessions and
task subagents in `RULES.md`; put one subagent's protocol in that agent's definition.

For package-specific guidance, choose one of these deliberately:

- A local AGENTS.md when rules apply to files in that subtree and normal work reads those files.
- A native `.omp/AGENTS.md` when package rules must load from an OMP configuration boundary.
- A root pointer when a workflow may act through tools that do not trigger contextual loading.

Keep one authoritative location per rule. Lower scopes reference higher scopes instead of copying
them.

## Write rules

- State the required behavior and the condition that triggers it.
- Use `MUST` or `MUST NOT` only for hard requirements.
- Replace vague qualities with an observable result or a real example path.
- Give the valid alternative when prohibiting an action.
- Omit prose that only restates structural enforcement.
- Keep primary-only delegation and user-facing behavior in AGENTS.md.

Register a skill in always-loaded instructions only when missing that skill causes repeated,
consequential errors. Put primary-only registrations in AGENTS.md and universal registrations in
RULES.md.

## Review

Before finalizing:

- Verify every path and command against the repository.
- Inspect history before restoring a removed instruction or workflow; absence may be intentional.
- Remove duplicated, stale, generic, and speculative guidance.
- Confirm each remaining rule has one authoritative home and a concrete failure it prevents.
- Check that the file helps an agent choose the next source without describing the repository file
  by file.
