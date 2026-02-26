---
name: subagent-authoring
description: Use when creating or modifying custom agent definitions
---

# Subagent Authoring

Load this skill when creating or modifying custom OpenCode agents. This skill documents our
conventions, not exhaustive OpenCode capabilities. Omissions are intentional.

## What Agents Are

Agents are specialized personas with specific models, prompts, tools, and permissions. They can
serve as primary entry points (user-facing) or subagents (invoked by other agents via the Task
tool).

## Definition Methods

Agents can be defined in two ways:

### Markdown Files

Place in `.opencode/agents/<name>.md` (project) or `~/.config/opencode/agents/<name>.md` (global):

```markdown
---
description: Reviews code for best practices and potential issues
mode: subagent
model: anthropic/claude-sonnet-4-5
tools:
  write: false
  edit: false
---

You are a code reviewer. Focus on security, performance, and maintainability.
```

### JSON Configuration

Define in `opencode.json`:

```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-5",
      "prompt": "You are a code reviewer. Focus on security, performance, and maintainability.",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}
```

## Frontmatter Fields

### Core Fields

| Field         | Type   | Description                                       |
|---------------|--------|---------------------------------------------------|
| `name`        | string | Agent identifier (defaults to filename)           |
| `description` | string | Brief description shown in UI (required)          |
| `mode`        | string | `primary`, `subagent`, or `all` (defaults to all) |
| `model`       | string | Provider/model identifier                         |
| `variant`     | string | Reasoning variant for this agent's model          |
| `prompt`      | string | System prompt (or `@./path.txt` to include file)  |

### Tool Permissions (deprecated)

The `tools` field is deprecated; use `permission` instead. Legacy `tools` entries are converted to
permissions internally.

```yaml
# Deprecated
tools:
  write: false
  edit: false
  bash: false
```

### Permissions

Control tool-level and skill-level permissions per agent. Values: `allow`, `deny`, `ask`.

```yaml
permission:
  edit: deny
  bash:
    "*": ask
    "git diff": allow
    "git log*": allow
  webfetch: deny
  skill:
    "*": "allow"
    "internal-*": "deny"
  task:
    "*": "deny"
    "my-subagent-*": "allow"
```

Bash and task permissions support glob patterns. Last matching rule wins.

### Behavior Options

| Field         | Type    | Description                                        |
|---------------|---------|----------------------------------------------------|
| `hidden`      | boolean | Hide from @ autocomplete menu (subagent only)      |
| `steps`       | integer | Max agentic iterations (`maxSteps` is deprecated)  |
| `disable`     | boolean | Set `true` to disable the agent                    |
| `temperature` | number  | LLM randomness (0.0-1.0)                           |
| `top_p`       | number  | Response diversity (0.0-1.0)                       |
| `color`       | string  | `#hex` or theme name (primary, accent, error, etc) |

### Reasoning Variants

Use the `variant` field to select a pre-defined reasoning configuration for the agent's model.
Available variants are model-specific:

| Provider/Model      | Variants                                            |
|---------------------|-----------------------------------------------------|
| Anthropic Opus 4.6  | `low`, `medium`, `high`, `max` (adaptive)           |
| Anthropic (other)   | `high`, `max` (fixed token budget)                  |
| OpenAI GPT-5 family | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` |
| Google Gemini 3     | `low`, `high`                                       |

```yaml
---
description: Deep reasoning agent
mode: subagent
model: anthropic/claude-opus-4-6
variant: medium
---
```

```json
{
  "agent": {
    "thinker": {
      "model": "anthropic/claude-opus-4-6",
      "variant": "high"
    }
  }
}
```

Variant takes highest priority in the options merge chain, overriding any provider passthrough
fields.

### Provider Passthrough Options

Unknown frontmatter fields pass through as model `options`. Use for provider-specific features when
variants don't cover your needs (e.g., custom token budgets).

```yaml
---
description: Agent with custom thinking budget
mode: subagent
model: anthropic/claude-sonnet-4-5
thinking:
  type: enabled
  budgetTokens: 8000
---
```

Prefer `variant` over manual passthrough when a matching variant exists.

## Agent Modes

### primary

User-facing agents selectable in the TUI. Use for main workflows.

```json
{
  "agent": {
    "build": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-5"
    }
  }
}
```

### subagent

Invoked programmatically by other agents via the Task tool. Not directly user-selectable.

```json
{
  "agent": {
    "code-reviewer": {
      "mode": "subagent"
    }
  }
}
```

### all

Both user-selectable and invocable by other agents.

```json
{
  "agent": {
    "docs-writer": {
      "mode": "all"
    }
  }
}
```

## Hidden Agents

Hide agents from the @ autocomplete menu while keeping them invocable:

```json
{
  "agent": {
    "internal-helper": {
      "mode": "subagent",
      "hidden": true
    }
  }
}
```

Use for utility agents that should only be called by other agents, never directly by users.

## Agent Structure Best Practices

### Essential Sections

A well-structured agent prompt should include:

**Workflow/Prerequisites**: Mandatory steps before starting work.

```markdown
## Workflow

1. Read the full diff before commenting
2. Check existing review comments to avoid duplicates
```

**Domain Ownership**: Which paths or concerns this agent handles.

```markdown
## Domain Ownership

- `src/components/` - React components
- `src/hooks/` - Custom hooks
- `*.test.tsx` - Test files
```

**Hard Constraints**: Non-negotiable rules with consequences.

```markdown
## Constraints

- NEVER approve PRs with failing CI
- MUST request changes for security issues
- MUST NOT comment on style if linter passes
```

**Verification Commands**: How to validate work.

````markdown
## Verification

```bash
npm run lint
npm run test
npm run build
```
````

**When Stuck**: Escape hatch for uncertainty.

```markdown
## When Stuck

- Ask a clarifying question
- Propose alternatives with tradeoffs
- Do not guess at intent
```

### Pointer to Skills

Reference skills for detailed knowledge rather than embedding it:

```markdown
Load the `csharp-coding` skill for C# patterns and idioms.
```

## CLI Creation

Create agents interactively:

```bash
opencode agent create
```

This guides you through:

1. Selecting save location (project or global)
2. Providing description
3. Generating system prompt
4. Selecting tools
5. Creating the markdown file

## Agent vs Skill Separation

**Agent (always loaded):**

- Workflow/prerequisites (mandatory steps)
- Domain ownership (which paths)
- Hard constraints (NEVER rules)
- Verification commands
- Pointer to skill

**Skill (loaded on demand):**

- Code examples and patterns
- Step-by-step procedures
- File templates
- Debugging guides
- Comprehensive reference

**Decision heuristic**: Is this needed in every conversation with this agent?

- Yes: Put in agent
- No, only for specific operations: Put in skill

## Validation Checklist

Before finalizing changes:

- [ ] Mode is explicitly set (primary, subagent, or all)
- [ ] Description is clear and concise
- [ ] Tool permissions match agent's purpose (read-only agents disable write/edit/bash)
- [ ] Hard constraints use RFC 2119 keywords (MUST, MUST NOT, NEVER)
- [ ] Skills referenced where detailed patterns live
- [ ] "When stuck" guidance included
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
