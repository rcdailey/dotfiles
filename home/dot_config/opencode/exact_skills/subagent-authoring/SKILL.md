---
name: subagent-authoring
description: >-
  Use when creating, editing, or refactoring custom OpenCode agent definitions (`.md` or
  `.md.tmpl` files in an agents directory, including chezmoi source forms). Triggers on any
  edit to an agent definition file. Do NOT use for AGENTS.md, SKILL.md, or slash commands.
---

# Subagent Authoring

Conventions for OpenCode agent definitions. Omissions intentional.

## What Agents Are

Specialized personas with models, prompts, tools, and permissions. Primary agents are user-facing;
subagents are invoked via the Task tool.

## Definition

Markdown files in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md`
(global). JSON alternative exists under `agent` in `opencode.json` with a `prompt` field; prefer
markdown.

## Frontmatter Fields

### Core

| Field         | Type    | Description                                      |
| ------------- | ------- | ------------------------------------------------ |
| `name`        | string  | Agent identifier (defaults to filename)          |
| `description` | string  | Drives caller delegation (required; see below)   |
| `mode`        | string  | `primary`, `subagent`, or `all` (default: `all`) |
| `model`       | string  | Provider/model identifier                        |
| `variant`     | string  | Reasoning variant (see table below)              |
| `prompt`      | string  | System prompt (or `@./path.txt` to include file) |
| `hidden`      | boolean | Hide from @ menu (subagent only)                 |

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

For subagents, the description is the caller's sole signal for delegation via the Task tool. Same
trigger-coverage discipline as skill descriptions (see `skill-authoring`): multiple phrasings,
explicit scope, negative triggers for fuzzy boundaries. Routing reinforcement for subagents lives in
the caller's `AGENTS.md` (primary agents delegate), not in the subagent's own file.

Subagent descriptions additionally MUST specify:

- **Caller protocol**: what the caller MUST pass (required inputs, structured format) and MUST NOT
  pass (context the agent infers). Thin protocols cause callers to over-specify defensively or
  under-specify and misroute.
- **Return contract**: what the caller should expect back (single message, structured report,
  success/failure shape, whether output is trustworthy without verification).

Primary agents have looser requirements; their description is surfaced in the TUI for the user, not
for programmatic routing.

Example (subagent):

```yaml
description: >-
  Reviews code for security, performance, and maintainability issues. Use when finalizing a PR,
  auditing a new module, or responding to review requests. Callers MUST pass: the file paths or
  PR number to review, the scope (security only, full review, etc.). MUST NOT pass: the diff
  itself (the agent reads it). Returns a single message with findings as bullets; no file
  writes. Do NOT use for style/lint concerns (use the linter) or commit message review.
```

### Behavior Options

| Field         | Type    | Description                                       |
| ------------- | ------- | ------------------------------------------------- |
| `steps`       | integer | Max agentic iterations (`maxSteps` is deprecated) |
| `disable`     | boolean | Set `true` to disable the agent                   |
| `temperature` | number  | LLM randomness (0.0-1.0)                          |
| `top_p`       | number  | Response diversity (0.0-1.0)                      |
| `color`       | string  | `#hex` or theme name (primary, accent, error)     |

### Reasoning Variants

| Provider/Model      | Variants                                            |
| ------------------- | --------------------------------------------------- |
| Anthropic Opus 4.6  | `low`, `medium`, `high`, `max` (adaptive)           |
| Anthropic (other)   | `high`, `max` (fixed token budget)                  |
| OpenAI GPT-5 family | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` |
| Google Gemini 3     | `low`, `high`                                       |

Variant takes highest priority in the options merge chain. Unknown frontmatter fields pass through
as provider-specific model `options`.

## Agent Modes

- **primary**: User-facing, selectable in TUI.
- **subagent**: Invoked programmatically via Task tool.
- **all**: Both.

Set `hidden: true` on subagents that should only be called by other agents.

## Prompt Structure

A well-structured prompt includes (not all required):

- **Workflow/prerequisites**: mandatory steps before starting
- **Domain ownership**: paths or concerns the agent handles
- **Hard constraints**: RFC 2119 rules (see `agents-authoring` for rule-writing conventions). Do not
  restate constraints already enforced by permissions.
- **Verification commands**: how to validate work
- **Output format**: what the agent produces (critical when callers consume the response)
- **When stuck**: escape hatch for uncertainty

Example:

````markdown
## Workflow

1. Read the full diff before commenting
2. Check existing review comments to avoid duplicates

## Constraints

NEVER approve PRs with failing CI. MUST request changes for security issues.
MUST NOT comment on style if linter passes.

## Output

Return a single message: summary (1-2 sentences), findings as bullets, recommended next steps.
Do not write results to files.

## When Stuck

Ask a clarifying question. Propose alternatives with tradeoffs. Do not guess at intent.
````

### Reference Material

Include tool command signatures the agent needs to act without discovery calls. Keep concise:
signatures and key flags. Standalone subagents (no companion skill) MUST have reference material
inline; extracting into a skill only one agent uses adds indirection without value. When a companion
skill exists, reference it by name instead of duplicating.

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
