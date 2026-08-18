---
name: subagent-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OMP task-agent definitions in Markdown,
  including `.omp/agents`, user agents, extension agents, and chezmoi source forms. Do NOT use for
  AGENTS.md, SKILL.md, or slash commands.
---

# Subagent Authoring

Agents justify a separate definition through a distinct role, permission boundary, model, or isolated
context. Put reusable procedures in skills instead of creating persona-only agents.

## Definition and source

Define project agents in `.omp/agents/<name>.md` and user agents in
`~/.omp/agent/agents/<name>.md`. In a generated configuration repository, edit the source template
and validate the rendered target; do not maintain both independently.

Common fields are:

- `name` and `description`: required identity and routing summary.
- `tools`: optional allowlist; `yield` is added automatically when restricted.
- `spawns`: optional `*`, CSV, or array of agents this agent may launch.
- `model`: one selector or an ordered fallback list; role aliases such as `@slow` are supported.
- `thinking-level`, `output`, `blocking`, `autoloadSkills`, `prewalk`, and `advisor`: optional runtime
  behavior.

Provider-specific fields and reasoning options change independently of OMP. Verify them against
the current provider and schema instead of preserving a model catalog here.

## Capability boundaries

Use `tools` and `spawns` to limit capabilities. OMP does not provide a per-agent command permission
matrix. Child sessions inherit global `tools.approval` and `bash.patterns`, then run headless with
approval mode set to `yolo`; inherited `deny` still blocks and `prompt` fails without a UI.

- Omit mutation tools from read-only agents when their work remains possible without them.
- Grant Bash only when dedicated tools cannot reach required verification.
- Allow only the skills and child agents required by the workflow.
- State behavioral restrictions that OMP cannot enforce in frontmatter, and do not present them as a
  security boundary.

## Routing contract

A subagent description must tell callers:

- when to delegate and when not to;
- required inputs and anything callers should omit;
- the result returned and whether the caller must verify it.

The prompt defines domain ownership, workflow boundaries, failure behavior, and output contract. It
must be self-contained about its own protocol, but it need not contain repository knowledge that the
agent is specifically responsible for discovering.

Reference a companion skill by name rather than copying its procedure. Include fixed tool syntax
only when the agent cannot perform its job without it and `--help` cannot supply it.

The prompt, allowed skills, readable files, and available tools must together provide enough
information to produce the return contract. Least privilege must not make the workflow impossible.
Task subagents inherit RULES.md but not AGENTS.md. Check inherited rules against the role. State a
narrow exception when the agent's valid output cannot satisfy an inherited workflow, such as an
out-of-repository artifact that cannot be committed.

## Review

- Confirm the name and description match how callers invoke the agent.
- Compare advertised work with effective permissions and available tools.
- Check inherited RULES.md instructions for requirements the role cannot or should not perform.
- Validate every caller and command against the agent's input contract.
- Confirm the agent can obtain required schemas and reference data within its permission boundary.
- Remove inherited rules, duplicated skill content, and generic persona text.
- Verify generated templates and rendered definitions agree.
- Test blocked behavior as well as allowed behavior for security boundaries.
