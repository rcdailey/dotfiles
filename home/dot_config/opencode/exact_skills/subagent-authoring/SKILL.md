---
name: subagent-authoring
description: Best practices for creating and configuring OpenCode custom agents
---

# Subagent Authoring

Load this skill when creating or modifying custom OpenCode agents.

## What Agents Are

Agents are specialized personas with specific models, prompts, tools, and permissions. They can
serve as primary entry points (user-facing) or subagents (invoked by other agents via the Task
tool).

## Definition Methods

Agents can be defined in two ways:

### Markdown Files

Place in `.opencode/agents/<name>.md` or `~/.config/opencode/agents/<name>.md`:

```markdown
---
description: Reviews code for best practices and potential issues
mode: subagent
model: anthropic/claude-sonnet-4-20250514
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
      "model": "anthropic/claude-sonnet-4-20250514",
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

| Field         | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `name`        | string | Agent identifier (defaults to filename)          |
| `description` | string | Brief description shown in UI                    |
| `mode`        | string | `primary`, `subagent`, or `all`                  |
| `model`       | string | Provider/model identifier                        |
| `prompt`      | string | System prompt (or `{file:./path.txt}`)           |

### Tool Permissions

```yaml
tools:
  write: true
  edit: true
  bash: true
```

Set to `false` to disable specific capabilities. Read-only agents should disable write, edit, and
bash.

### Skill Permissions

Control which skills the agent can load:

```yaml
permission:
  skill:
    "*": deny
    specific-skill: allow
```

### Behavior Options

| Field      | Type    | Description                              |
|------------|---------|------------------------------------------|
| `hidden`   | boolean | Hide from @ autocomplete menu            |
| `maxSteps` | integer | Maximum tool call iterations             |
| `steps`    | array   | Predefined workflow steps                |

### Model-Specific Options

Unknown frontmatter fields pass through as model options. Use for provider-specific features.

**Anthropic extended thinking:**

```yaml
---
description: Agent with extended thinking
mode: subagent
model: anthropic/claude-opus-4-5
thinking:
  type: enabled
  budgetTokens: 16000
---
```

**OpenAI reasoning effort:**

```yaml
---
description: Agent with reasoning
mode: subagent
model: openai/o3
reasoningEffort: high
---
```

## Agent Modes

### primary

User-facing agents selectable in the TUI. Use for main workflows.

```json
{
  "agent": {
    "build": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-20250514"
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

1. Load the `pr-review` skill before reviewing code
2. Read the full diff before commenting
3. Check existing review comments to avoid duplicates
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
