---
name: subagent-authoring
description: >-
  Use when creating, editing, or refactoring custom OpenCode agent definitions (`.md` or
  `.md.tmpl` files in an agents directory, including chezmoi source forms). Triggers on any
  edit to an agent definition file. Do NOT use for AGENTS.md, SKILL.md, or slash commands.
---

# Subagent Authoring

Conventions for OpenCode agent definitions. Omissions intentional. All authored content MUST follow
the Authoring rules in global AGENTS.md.

## What Agents Are

Specialized personas with models, prompts, tools, and permissions. Primary agents are user-facing;
subagents are invoked via the Task tool.

## Definition

Markdown files in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md`
(global). JSON alternative exists under `agent` in `opencode.json` with a `prompt` field; prefer
markdown.

## Frontmatter Fields

### Core

- `name` (string): agent identifier (defaults to filename)
- `description` (string): drives caller delegation (required; see below)
- `mode` (string): `primary`, `subagent`, or `all` (default: `all`)
- `model` (string): provider/model identifier
- `variant` (string): reasoning variant (see below)
- `prompt` (string): system prompt (or `@./path.txt` to include file)
- `hidden` (boolean): hide from @ menu (subagent only)

### Permissions

Tool-level and skill-level access; values `allow`, `deny`, `ask`. Bash and task permissions support
glob patterns; last matching rule wins.

```yaml
permission:
  edit: deny
  bash:
    "*": ask
    "git diff": allow
    "git log*": allow
  webfetch: deny
  skill:
    "*": allow
    "internal-*": deny
  task:
    "*": deny
    "my-subagent-*": allow
```

The deprecated `tools` field converts to permissions internally; prefer `permission`.

### Writing the Description

Same trigger-coverage discipline as skill descriptions (see `skill-authoring`). Routing
reinforcement lives in the caller's `AGENTS.md`, not the subagent's own file.

Subagent descriptions additionally MUST specify:

- **Caller protocol**: what to pass and what to omit (required inputs, structured format).
- **Return contract**: what the caller gets back (shape, trustworthiness).

Primary agent descriptions are looser; surfaced in TUI for humans, not programmatic routing.

### Behavior Options

- `steps` (integer): max agentic iterations (`maxSteps` is deprecated)
- `disable` (boolean): set `true` to disable
- `temperature` (number): LLM randomness (0.0-1.0)
- `top_p` (number): response diversity (0.0-1.0)
- `color` (string): `#hex` or theme name (primary, accent, error)

### Reasoning Variants

- Anthropic Opus 4.6: `low`, `medium`, `high`, `max` (adaptive)
- Anthropic (other): `high`, `max` (fixed token budget)
- OpenAI GPT-5 family: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`
- Google Gemini 3: `low`, `high`

Variant takes highest priority in the options merge chain. Unknown frontmatter fields pass through
as provider-specific model `options`.

## Agent Modes

- **primary**: User-facing, selectable in TUI.
- **subagent**: Invoked programmatically via Task tool.
- **all**: Both.

Set `hidden: true` on subagents that should only be called by other agents.

## Prompt Structure

Cover (not all required): workflow/prerequisites, domain ownership, hard constraints (RFC 2119; see
`agents-authoring`), verification commands, output format, when stuck. Do not restate constraints
already enforced by permissions.

### Reference Material

Include tool command signatures the agent needs to act without discovery calls. Standalone subagents
MUST have reference inline; when a companion skill exists, reference by name instead.

The test: can the agent do its job from the prompt alone? If not, add the missing reference.

## Validation Checklist

- [ ] Mode explicitly set (primary, subagent, or all)
- [ ] Description includes multiple trigger phrasings and explicit scope
- [ ] Description includes negative triggers for fuzzy boundaries
- [ ] Subagent descriptions specify caller protocol (inputs to pass, inputs to omit)
- [ ] Subagent descriptions specify return contract
- [ ] Tool permissions match purpose (read-only agents deny write/edit/bash)
- [ ] Hard constraints use RFC 2119 keywords
- [ ] Agent can act from prompt alone (no discovery tool calls)
- [ ] Tool references inline and concise
- [ ] "When stuck" guidance included
