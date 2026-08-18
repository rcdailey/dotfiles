---
name: command-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OMP file slash commands; writing or revising
  command frontmatter, arguments, expansion, or orchestration.
  Triggers on phrases like "new slash command", "add a /command", "edit the command file",
  or any edit to files in a commands directory (including chezmoi source forms). Do NOT
  use for AGENTS.md, SKILL.md, or agent definitions.
---

# Command Authoring

Commands are thin user-facing entry points for repeatable prompts. Put reusable procedures in skills
and specialized execution contracts in agents.

## Definition

Place project commands in `.omp/commands/<name>.md` and user commands in
`~/.omp/agent/commands/<name>.md`. The filename becomes the slash command.

```yaml
---
description: Brief purpose shown in command completion
---
```

- `description` is required for authored native commands.
- Keep agent dispatch in the command body through `task`; file frontmatter does not select an agent.

The body supports `$ARGUMENTS`, `$@`, positional `$1` values, and argument slices such as
`$@[2:3]`. OMP parses single- and double-quoted arguments but does not implement backslash escapes.

## Write the command

- Start with the requested outcome and define fallback behavior for missing arguments.
- Reference a skill or agent instead of copying its workflow.
- State output shape and stop conditions only when they affect execution.
- Dispatch discovery-heavy or large-output work with the `task` tool when isolation is valuable.
- Keep simple commands simple; headings and phases are optional.

The selected agent must support every mode the command advertises. Pass all required and applicable
optional inputs. Handle each documented return status, including blocked, partial, and retry paths,
without inventing alternate behavior in the command layer.

Task agents remain addressable after yielding. Keep the returned agent ID when a command supports
follow-up work, then continue that agent through `hub` instead of spawning a replacement.

Keep an interactive orchestration command on the primary agent when it must gather input or confirm
decisions before delegation. Do not bind the command to the eventual worker merely because that
worker performs the final step.

## Arguments and injected context

Treat expanded arguments as untrusted text. Let the agent validate them before running tools. Keep
file commands as prompt entry points; use an extension command when execution must happen before an
LLM turn or needs direct session control.

## Review

- Verify frontmatter and placeholder behavior against current OMP documentation.
- Compare the command with the agent's required inputs, optional inputs, statuses, and recovery
  behavior.
- Check empty, malformed, and adversarial arguments.
- Bound injected output and isolate large workflows.
- Remove duplicated skill, agent, and global instructions.
- Confirm the command does not override a built-in command unintentionally.
