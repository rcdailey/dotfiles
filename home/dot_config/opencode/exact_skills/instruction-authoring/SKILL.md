---
name: instruction-authoring
description: >-
  Use when proposing, drafting, creating, editing, refactoring, or reviewing OpenCode instructions:
  AGENTS.md, shared `.chezmoitemplates/opencode-*.md` partials, primary-agent prompt prose, SKILL.md
  or a skill directory, agent definitions or `opencode.json` agent entries, and slash commands or
  files in a commands directory, including chezmoi source forms and edits made while fixing agent
  permissions or behavior.
---

# Instruction Authoring

Apply the active Authoring policy and the shared rules below, then the section for the artifact.

## Shared rules

### Placement

Apply this order to every candidate instruction:

1. Delete it if code, tool help, configuration, or ordinary conventions already reveal it.
2. Enforce it with permissions, tests, schemas, hooks, or linters when deterministic.
3. Put a recurring task procedure in a skill, an execution contract in an agent, a user entry point
   in a command, and detailed reference material in documentation.
4. Keep it in AGENTS.md only when it is durable, consequential, and broadly applicable.

Every agent receives global AGENTS.md. Scope primary-only rules explicitly, or put them in the
primary prompt. Register a skill in always-loaded instructions only after repeated consequential
misses; put primary-only registration in the primary prompt.

### Writing

- State the required behavior and the condition that triggers it.
- Use `MUST` or `MUST NOT` only for hard requirements.
- Replace vague qualities with an observable result or a real example path.
- Give the valid alternative when prohibiting an action.
- Omit prose that only restates structural enforcement.
- Reference a skill, agent, or higher-scope rule instead of copying it.
- For CLI tools, teach sequencing and non-obvious semantics; include fixed syntax only when required
  to act and unavailable from `--help`.
- Include an example only when it communicates a contract better than rules; it MUST obey the rules
  it teaches, as must disposable checks.

### Review

- Verify every path, command, frontmatter field, and placeholder against the repository and current
  OpenCode documentation.
- Inspect current use and history before restoring a removed instruction or workflow; absence may be
  intentional, and existing files do not prove a workflow is active.
- Remove duplicated, stale, generic, speculative, and inferable guidance, including rules inherited
  from AGENTS.md, skills, or agents.
- Confirm each remaining rule has one authoritative home and prevents a concrete, current failure.
- Before removing a contract, confirm consumers can read it elsewhere within their permissions;
  otherwise keep its minimal canonical form.
- In generated configuration, edit the source template and validate the rendered target; do not
  maintain both independently.

## AGENTS.md and primary prompts

AGENTS.md contains only non-obvious, durable rules for its effective scope; it is not a repository
manual. Keep unusual commands, architectural boundaries, operational hazards, and only enough map to
authoritative files to direct the next read.

OpenCode loads global AGENTS.md and the first project rule file found above the working directory.
Its read tool also injects applicable child AGENTS.md files above a target file; shell reads do not.
For package-specific guidance, choose deliberately:

- A local AGENTS.md when rules apply to files in that subtree and normal work reads those files.
- The `instructions` setting when package rules must load before any file read.
- A root pointer when a workflow may act through tools that do not trigger contextual loading.

## Skills

Create a skill only for a recurring procedure that should not load for unrelated work. Keep
selection metadata in frontmatter, every-invocation procedure in SKILL.md, and optional detail in
referenced files or scripts.

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
  directory and is unique across discovery locations.
- `description`: required, 1-1024 characters. Wrap multi-line values as a folded block (`>-`); a
  plain scalar containing `: ` is invalid YAML, and OpenCode silently drops the skill.
- `license`, `compatibility`, and string-to-string `metadata`: optional.
- Unknown fields are ignored; do not invent behavioral fields.

The description selects the skill before its body loads. Start with `Use when`; state triggers,
likely user phrasing, governed paths, and tool names, not the procedure. Prefer precision over an
exhaustive keyword list. Add a negative trigger only for a neighbor with an ambiguous boundary.

The body includes only purpose, inputs, procedure, failure behavior, and verification the agent
cannot infer. It must support action without broad preliminary discovery; task-specific repository
discovery remains valid.

- Move large, separable reference material into `references/`.
- Use a script when deterministic transformation or validation is safer than prose.
- Delete unused references and scripts rather than preserving an empty structure.

## Commands

Commands are thin user-facing entry points. Place Markdown commands in
`.opencode/commands/<name>.md` or `~/.config/opencode/commands/<name>.md`; the filename becomes the
slash command. Confirm it does not override a built-in command unintentionally.

```yaml
---
description: Brief purpose shown in command completion
agent: build
subagent: true
---
```

- `description` is required; `agent` and `model` are optional overrides.
- A subagent target runs in a child by default; `subagent: false` disables that behavior.
- `subagent: true` isolates execution even when the selected agent is primary. Use it for
  discovery-heavy or large-output work that does not need the primary conversation.
- The body supports `$ARGUMENTS`, positional `$1` values, shell output via `` !`command` ``, and
  file inclusion via `@path`.

Write the body:

- Start with the requested outcome and define fallback behavior for missing arguments.
- State output shape and stop conditions only when they affect execution.
- Keep simple commands simple; headings and phases are optional.
- Ensure the selected agent supports the execution mode. Pass every required input and handle each
  documented return status and recovery path without inventing command-layer behavior.
- Keep interactive orchestration on the primary agent when it must gather input or confirm
  decisions.

Treat arguments as untrusted; check empty, malformed, and adversarial values. Never interpolate
placeholders into shell-output expressions; let the agent validate arguments before running tools.
Shell-output expressions execute in the project root before their output enters the prompt:

- Keep them read-only, deterministic, and bounded; never run formatters, migrations, installs, or
  other mutating commands through injection.
- Use an agent tool call when output depends on user input or requires error handling.
- Avoid `@path` inclusion for large files; instruct the agent to read targeted content instead.

## Agent definitions

Create an agent only for a distinct role, permission boundary, model, or isolated context; do not
create persona-only agents or add generic persona text.

Define agents in `.opencode/agents/<name>.md`, `~/.config/opencode/agents/<name>.md`, or the
`agents` section of `opencode.json`. Required routing field: `description`. Common optional fields
are `mode`, `model`, `disabled`, `color`, `hidden`, `permissions`, and `request.body`. Join a model
and variant as `provider/model#variant`. `mode` defaults to `all`; `hidden` affects only subagent
autocomplete. Verify provider options against the current provider and schema; do not preserve a
model catalog.

Permissions:

- Use ordered `permissions`; the last matching permission wins, so put wildcards first. Use `shell`
  and `subagent` action names, not the V1 `bash` and `task` names.
- Start specialist tool access from deny-by-default permissions. Existing shell policies are
  deliberate; do not tighten them without explicit approval.
- Broad shell access is not a read-only security boundary; check redirection and indirect mutation
  paths when granting it.
- Define permitted effects, including scratch writes and test artifacts, separately from source
  edits.
- Allow only the skills and subagents the workflow requires.
- Use permissions instead of repeating an enforceable prohibition in prose.

Routing contract:

- A subagent description states when to delegate, required and omitted inputs, the returned result,
  and whether callers must verify it. Confirm mode and description match how callers invoke it.
- The prompt defines ownership, workflow boundaries, failure behavior, and output contract.
- The prompt, skills, readable files, and tools must support the return contract, including required
  schemas and reference data, without defeating least privilege. Compare advertised work with
  effective permissions and available tools.
- Check inherited rules against the role; state the narrow exception when valid work cannot satisfy
  one.
- Validate every caller and command against the agent's input contract.
- Test blocked behavior as well as allowed behavior for security boundaries.
