---
name: subagent-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing an OpenCode agent definition or
  `opencode.json` agent entry, including chezmoi source forms. Do not use for AGENTS.md, skills, or
  commands.
---

# Subagent Authoring

Create an agent only for a distinct role, permission boundary, model, or isolated context. Put
reusable procedures in skills; do not create persona-only agents.

Density is part of correctness. After preserving required behavior, MUST remove every sentence,
example, heading, or section that does not change routing, ownership, permissions, workflow, failure
handling, or return contract. Tighten the rest without obscuring conditions or alternatives.

## Definition and source

Define agents in `.opencode/agents/<name>.md`, `~/.config/opencode/agents/<name>.md`, or the `agent`
section of `opencode.json`. In a generated configuration repository, edit the source template and
validate the rendered target; do not maintain both independently.

Required routing field: `description`. Common optional fields: `mode`, `model`, `variant`,
`temperature`, `top_p`, `steps`, `disable`, `color`, `hidden`, and `permission`. `mode` defaults to
`all`; `hidden` affects only subagent autocomplete.

Verify provider options against the current provider and schema; do not preserve a model catalog.

## Permissions

Use `permission`; `tools` is deprecated. Last matching permission wins, so put wildcards first.

- Start read-only and specialist agents from deny-by-default permissions.
- Deny edits and mutation-capable Bash commands for read-only roles.
- Allow only the skills and subagents required by the workflow.
- Use permissions instead of repeating an enforceable prohibition in prose.
- Check shell redirection and indirect mutation paths when granting Bash access.

## Routing contract

A subagent description states when to delegate, required and omitted inputs, the returned result,
and whether callers must verify it.

The prompt defines ownership, workflow boundaries, failure behavior, and output contract.

Reference companion skills instead of copying them. Include fixed tool syntax only when required to
act and unavailable from `--help`.

The prompt, skills, readable files, and tools must support the return contract without defeating
least privilege. Check inherited rules against the role; state the narrow exception when valid work
cannot satisfy one.

## Review

- Confirm the mode and description match how callers invoke the agent.
- Compare advertised work with effective permissions and available tools.
- Check inherited instructions for requirements the role cannot or should not perform.
- Validate every caller and command against the agent's input contract.
- Confirm the agent can obtain required schemas and reference data within its permission boundary.
- Remove inherited rules, duplicated skill content, and generic persona text.
- Verify generated templates and rendered definitions agree.
- Test blocked behavior as well as allowed behavior for security boundaries.
