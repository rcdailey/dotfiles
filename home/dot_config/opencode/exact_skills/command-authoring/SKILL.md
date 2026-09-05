---
name: command-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OpenCode slash commands or files in a
  commands directory, including chezmoi source forms. Do not use for AGENTS.md, skills, or agent
  definitions.
---

# Command Authoring

Commands are thin user-facing entry points. Put reusable procedures in skills and execution
contracts in agents.

Apply the active Authoring policy; this skill governs command routing and input handling.

## Definition

Place Markdown commands in `.opencode/commands/<name>.md` or
`~/.config/opencode/commands/<name>.md`. The filename becomes the slash command.

```yaml
---
description: Brief purpose shown in command completion
agent: build
subtask: true
---
```

- `description` is required.
- `agent` and `model` are optional overrides.
- A subagent target runs as a subtask by default; `subtask: false` disables that behavior.
- `subtask: true` isolates execution even when the selected agent is primary.

The body supports `$ARGUMENTS`, positional `$1` values, shell output via `` !`command` ``, and file
inclusion via `@path`.

## Write the command

- Start with the requested outcome and define fallback behavior for missing arguments.
- Reference a skill or agent instead of copying its workflow.
- State output shape and stop conditions only when they affect execution.
- Use `subtask: true` for discovery-heavy or large-output work that does not need the primary
  conversation.
- Keep simple commands simple; headings and phases are optional.

Ensure the selected agent supports the execution mode. Pass every required input and handle each
documented return status without inventing command-layer behavior.

Keep interactive orchestration on the primary agent when it must gather input or confirm decisions.

## Arguments and injected context

Treat arguments as untrusted. Never interpolate placeholders into shell-output expressions; let the
agent validate arguments before running tools.

Shell-output expressions execute in the project root before their output enters the prompt:

- Keep them read-only, deterministic, and bounded.
- Do not run formatters, migrations, installs, or other mutating commands through injection.
- Use an agent tool call when output depends on user input or requires error handling.
- Avoid `@path` inclusion for large files; instruct the agent to read targeted content instead.

## Review

- Verify frontmatter and placeholder behavior against current OpenCode documentation.
- Compare the command with the agent's inputs, statuses, and recovery behavior.
- Check empty, malformed, and adversarial arguments.
- Bound injected output and isolate large workflows.
- Remove duplicated skill, agent, and global instructions.
- Confirm the command does not override a built-in command unintentionally.
