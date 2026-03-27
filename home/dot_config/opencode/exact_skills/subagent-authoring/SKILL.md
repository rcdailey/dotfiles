---
name: subagent-authoring
description: Use when creating or modifying custom agent definitions
---

# Subagent Authoring

Conventions for defining custom OpenCode agents. Omissions are intentional.

## What Agents Are

Agents are specialized personas with specific models, prompts, tools, and permissions. They serve as
primary entry points (user-facing) or subagents (invoked by other agents via the Task tool).

## Definition Methods

### Markdown Files (preferred)

Place in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md` (global):

```markdown
---
description: Reviews code for best practices and potential issues
mode: subagent
model: anthropic/claude-sonnet-4-5
permission:
  edit: deny
---

You are a code reviewer. Focus on security, performance, and maintainability.
```

### JSON Configuration

Define in `opencode.json` under the `agent` key. Same fields as frontmatter, with `prompt` for the
body text. Use when you need all agents in one file.

## Frontmatter Fields

### Core

| Field         | Type    | Description                                      |
| ------------- | ------- | ------------------------------------------------ |
| `name`        | string  | Agent identifier (defaults to filename)          |
| `description` | string  | Brief description shown in UI (required)         |
| `mode`        | string  | `primary`, `subagent`, or `all` (default: `all`) |
| `model`       | string  | Provider/model identifier                        |
| `variant`     | string  | Reasoning variant (see table below)              |
| `prompt`      | string  | System prompt (or `@./path.txt` to include file) |
| `hidden`      | boolean | Hide from @ menu (subagent only)                 |

### Permissions

Control tool-level and skill-level access. Values: `allow`, `deny`, `ask`. Bash and task permissions
support glob patterns; last matching rule wins.

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

The deprecated `tools` field (boolean per tool) is converted to permissions internally. Prefer
`permission` for new agents.

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

Variant takes highest priority in the options merge chain. Prefer `variant` over manual passthrough.
Unknown frontmatter fields pass through as provider-specific model `options` (e.g., custom thinking
budgets).

## Agent Modes

- **primary**: User-facing, selectable in TUI. Use for main workflows.
- **subagent**: Invoked programmatically via Task tool. Not directly user-selectable.
- **all**: Both user-selectable and invocable by other agents.

Set `hidden: true` on subagents that should only be called by other agents.

## Prompt Structure

A well-structured agent prompt includes (not all required for every agent):

- **Workflow/prerequisites**: Mandatory steps before starting work
- **Domain ownership**: Which paths or concerns this agent handles
- **Hard constraints**: Non-negotiable rules using RFC 2119 keywords (MUST, NEVER)
- **Verification commands**: How to validate work
- **Output format**: What the agent produces (critical when callers consume the response)
- **When stuck**: Escape hatch for uncertainty

Example combining these elements:

````markdown
## Workflow

1. Read the full diff before commenting
2. Check existing review comments to avoid duplicates

## Constraints

NEVER approve PRs with failing CI. MUST request changes for security issues.
MUST NOT comment on style if linter passes.

## Output

Return a single message: summary (1-2 sentences), findings as bullets, recommended
next steps. Do not write results to files.

## When Stuck

Ask a clarifying question. Propose alternatives with tradeoffs. Do not guess at intent.
````

### Reference Material

Include tool command signatures the agent needs to act without discovery calls. Keep concise:
signatures and key flags, not exhaustive docs. Reference shared skills by name instead of
duplicating content.

The test: can the agent do its job from the prompt alone? If not, add the missing reference. If it
can, don't add more.

## What Belongs Where

Include in the agent prompt what it needs to act correctly. Standalone subagents (no companion
skill) MUST have reference material inline; extracting into a skill only one agent uses adds
indirection without value. When a companion skill exists, reference it by name.

## Validation Checklist

- [ ] Mode is explicitly set (primary, subagent, or all)
- [ ] Description is clear and concise
- [ ] Tool permissions match agent's purpose (read-only agents deny write/edit/bash)
- [ ] Hard constraints use RFC 2119 keywords (MUST, MUST NOT, NEVER)
- [ ] Agent can act from prompt alone (no discovery tool calls needed)
- [ ] Tool references are inline and concise (not deferred to --help)
- [ ] "When stuck" guidance included
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
