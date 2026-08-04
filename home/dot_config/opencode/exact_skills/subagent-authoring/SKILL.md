---
name: subagent-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OpenCode agent definitions in Markdown
  (`.md`, `.md.tmpl`) or the `agent` section of `opencode.json`, including primary, subagent, and
  `all` modes and chezmoi source forms. Do NOT use for AGENTS.md, SKILL.md, or slash commands.
---

# Subagent Authoring

Agents justify a separate definition through a distinct role, permission boundary, model, or isolated
context. Put reusable procedures in skills instead of creating persona-only agents.

## Definition and source

Define agents in `.opencode/agents/<name>.md`, `~/.config/opencode/agents/<name>.md`, or the `agent`
section of `opencode.json`. In a generated configuration repository, edit the source template and
validate the rendered target; do not maintain both independently.

Common fields are:

- `description`: required routing summary.
- `mode`: `primary`, `subagent`, or `all`; defaults to `all`.
- `model`, `temperature`, `top_p`, `steps`, `disable`, and `color`: optional behavior settings.
- `hidden`: removes a subagent from user autocomplete, not programmatic invocation.
- `permission`: tool, Bash, skill, task, and external-directory access.

Provider-specific fields and reasoning options change independently of OpenCode. Verify them against
the current provider and schema instead of preserving a model catalog here.

## Permissions

Use `permission`; `tools` is deprecated. Permission patterns use last-match precedence, so put a
wildcard before narrower rules.

- Start read-only and specialist agents from deny-by-default permissions.
- Deny edits and mutation-capable Bash commands for read-only roles.
- Allow only the skills and subagents required by the workflow.
- Use permissions instead of repeating an enforceable prohibition in prose.
- Check shell redirection and indirect mutation paths when granting Bash access.

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
Check inherited repository and global rules against the role. State a narrow exception when the
agent's valid output cannot satisfy an inherited workflow, such as an out-of-repository artifact
that cannot be committed.

## Review

- Confirm the mode and description match how callers invoke the agent.
- Compare advertised work with effective permissions and available tools.
- Check inherited instructions for requirements the role cannot or should not perform.
- Validate every caller and command against the agent's input contract.
- Confirm the agent can obtain required schemas and reference data within its permission boundary.
- Remove inherited rules, duplicated skill content, and generic persona text.
- Verify generated templates and rendered definitions agree.
- Test blocked behavior as well as allowed behavior for security boundaries.
