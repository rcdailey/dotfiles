---
name: instruction-authoring
description: >-
  Use when proposing, drafting, creating, editing, refactoring, or reviewing model instructions:
  AGENTS.md, PRIMARY.md, CLAUDE.md, SYSTEM.md, APPEND_SYSTEM.md, SKILL.md or a skill directory, pi
  prompt templates (slash commands in a prompts directory), or subagent agent files, including
  chezmoi source forms and edits that arise mid-task.
---

# Instruction Authoring

Apply the shared rules to every artifact, then the section for the artifact type.

## Shared rules

### Placement

Apply this order to every candidate instruction:

1. Delete it if code, tool help, configuration, or ordinary conventions already reveal it.
2. Enforce it with permissions, tests, schemas, hooks, or linters when deterministic.
3. Put a recurring, nameable procedure in a skill and reference material in documentation.
4. Keep it in AGENTS.md only when it is durable, consequential, and broadly applicable.

Keep one authoritative location per concept; lower scopes reference higher scopes. Register a skill
in always-loaded instructions only after repeated consequential misses.

### Writing

- MUST use minimum tokens. Every word earns its place; bullet lists over paragraphs.
- MUST generalize from the concrete task. Strip scenario-specific details (file types, domain
  objects, tool names) that won't apply to future work.
- State the required behavior and the condition that triggers it.
- Use `MUST` or `MUST NOT` only for hard requirements.
- Replace vague qualities with an observable result or a real example path.
- Give the valid alternative when prohibiting an action.
- Omit prose that only restates structural enforcement.
- Cross-reference another artifact instead of copying it.
- Include one minimal example only when it communicates a contract better than rules. Examples MUST
  obey the rules they teach.

### Review

MUST self-review the draft against these rules before writing; tighten any violation.

- Verify every path, command, and frontmatter field against the repository and current docs.
- Inspect history before restoring a removed instruction or workflow; absence may be intentional.
- Remove duplicated, stale, generic, speculative, and inferable guidance at every scope.
- Confirm each remaining rule has one authoritative home and a concrete failure it prevents.
- Before removing a contract, confirm its consumers can read it elsewhere within their permissions.
- In generated configuration, edit the source and validate the rendered target.

## AGENTS.md and system prompt files

AGENTS.md holds only non-obvious, durable rules for its scope. It is not a repository manual. Keep
unusual commands, architectural boundaries, operational hazards, and a small map to authoritative
files only when they prevent a known failure.

pi loads `~/.pi/agent/AGENTS.md` plus context files in the working directory and every parent, never
child directories. `AGENTS.override.md` replaces context files in its own directory only. Context
files need no project trust; `.pi/SYSTEM.md` (replaces pi's prompt) and `.pi/APPEND_SYSTEM.md` do.

For package-specific guidance, choose deliberately:

- A local AGENTS.md when sessions for that package start in its directory.
- A root pointer to the package file when sessions start at the repository root.
- A skill when the rules apply only to a nameable task.

Subagent children inherit global and project AGENTS.md, so write it for every agent. Put rules for
the main session only (chatting with the user, orchestrating subagents) in `~/.pi/agent/PRIMARY.md`;
the `primary-instructions` extension adds it to the main session's system prompt and skips children.

## Skills

Create a skill only for a recurring procedure that should not load for unrelated work. Existing
files do not prove the workflow is active; inspect current use before restoring one.

pi discovers skills recursively under `~/.pi/agent/skills/`, `~/.agents/skills/`, `.pi/skills/`
(after trust), and `.agents/skills/` in the working directory and its ancestors up to the repository
root. A name collision keeps the first skill found.

- `name`: required, 1-64 lowercase alphanumeric characters separated by single hyphens; matches its
  directory.
- `description`: required, 1-1024 characters. Wrap multi-line values as a folded block (`>-`); a
  plain scalar containing `: ` is invalid YAML, and pi does not load the skill.
- `disable-model-invocation: true`: only `/skill:<name>` loads the skill.
- `license`, `compatibility`, `metadata`, and experimental `allowed-tools`: optional. Do not invent
  behavioral fields.

The description selects the skill before its body loads. Start with `Use when`; state triggers,
governed paths, and boundaries, not the procedure. Add a negative trigger only for an ambiguous
neighbor. Subagent children inherit the full skill catalog; restrict an agent's skills with `skill:`
rules in its `permission:` frontmatter.

The body holds only purpose, inputs, procedure, failure behavior, and verification the agent cannot
infer. It must support action without broad preliminary discovery.

- For CLI tools, teach sequencing and non-obvious semantics; defer syntax to `--help`.
- Move large, separable reference material into `references/`.
- Use a script when deterministic transformation or validation is safer than prose.
- Delete unused references and scripts.

After `/reload`, check startup diagnostics.

## Prompt templates

Templates are thin user-facing entry points. Put reusable procedures in skills and execution
contracts in agents.

Place templates in `~/.pi/agent/prompts/<name>.md` or `.pi/prompts/<name>.md` (after trust); only
direct `.md` children load. The filename becomes the command; confirm it does not collide with a
built-in, extension, or `/skill:` command.

```yaml
---
description: Brief purpose shown in command completion
argument-hint: "<required> [optional]"
---
```

The body supports `$1`, `$@`/`$ARGUMENTS`, `${1:-default}`, `${@:-default}`, and `${@:N[:L]}` with
shell-like quoting. There is no agent, model, shell-output, or file-inclusion syntax. Use
`pi.registerCommand` in an extension when the entry point needs code, UI, or deterministic behavior.

- Start with the requested outcome and define fallback behavior for missing arguments.
- Treat arguments as untrusted; let the agent validate them before passing them to tools.
- State output shape and stop conditions only when they affect execution.
- Delegate discovery-heavy or large-output work to a named subagent. Pass every required input and
  handle each documented return status.
- Keep interactive orchestration on the primary agent when it must gather input or confirm.
- Check empty, malformed, and adversarial arguments.

## Subagent definitions

Create an agent only for a distinct role, permission boundary, model, or isolated context; do not
create persona-only agents.

Agents run on `@gotgenes/pi-subagents`. Define them in `~/.pi/agent/agents/<name>.md` or
`.pi/agents/<name>.md`; the project file wins. The filename is the agent type; a same-name file
replaces a default agent (`general-purpose`, `Explore`, `Plan`), and `enabled: false` disables one.
All frontmatter is optional: `description`, `display_name`, `tools`, `model`, `thinking`,
`max_turns`, `prompt_mode`, `inherit_context`, `run_in_background`, `enabled`, `locked`, plus
pi-permission-system's `permission:`. Read the package's `docs/configuration.md` for semantics; do
not preserve a model catalog.

Prompt assembly:

- A child inherits the parent's pi preamble and `<project_context>` (all AGENTS.md files) byte for
  byte. Pi rebuilds skills and the working directory for the child, and the child's own extensions
  rebuild their prompt additions.
- `prompt_mode: append` (default) wraps the body in `<agent_instructions>` as a parent twin;
  `replace` appends the body last with the final say. Neither removes AGENTS.md.
- `inherit_context: true` forks the parent conversation into the child.
- Callers can override `model`, `thinking`, `max_turns`, `inherit_context`, and `run_in_background`;
  list fields in `locked` to prevent that.

Permissions:

- `tools` is the complete allowlist, including extension tools; `none` grants no tools.
- Children load the parent's extensions, so global permission rules, guards, and reminders apply.
  Exclude whole packages with `excludedExtensionPackages` in `~/.pi/agent/subagents.json`.
- `permission:` frontmatter layers over the global pi-permission-system config with the same
  surfaces, including `bash` patterns and `skill:` rules; last matching rule wins. It accepts
  scalars and nested maps only. An `ask` forwards to the user and pauses the child.
- Existing shell policies are deliberate; do not tighten them without explicit approval. Broad shell
  access is not a read-only boundary; check redirection and indirect mutation paths.
- Define permitted effects, including scratch writes and test artifacts, separately from source
  edits.
- Deny the `subagent` tool unless the workflow nests agents.

The description states when to delegate, required inputs, the returned result, and whether callers
must verify it. The prompt defines ownership, workflow boundaries, failure behavior, and output
contract. Its prompt, skills, readable files, and tools must support that contract without defeating
least privilege.

- Check inherited rules against the role; state the narrow exception when valid work cannot satisfy
  one.
- Validate every caller and prompt template against the agent's input contract.
- Test blocked behavior as well as allowed behavior for security boundaries.
