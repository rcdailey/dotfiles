---
name: command-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OpenCode custom slash commands;
  writing or revising command frontmatter, arguments, agent routing, or permissions.
  Triggers on phrases like "new slash command", "add a /command", "edit the command file",
  or any edit to files in a commands directory (including chezmoi source forms). Do NOT
  use for AGENTS.md, SKILL.md, or agent definitions.
---

# Command Authoring

Conventions for OpenCode custom commands. Omissions intentional. All authored content MUST follow
the Authoring rules in global AGENTS.md.

## Command Anatomy

### File Location

- **Global**: `~/.config/opencode/commands/<name>.md`
- **Per-project**: `.opencode/commands/<name>.md`

The filename (without `.md`) becomes the `/command-name`.

### Frontmatter

```yaml
---
description: Brief description shown in TUI autocomplete
agent: plan          # optional: which agent executes (defaults to current)
model: anthropic/claude-sonnet-4-5  # optional: override model
subtask: true        # optional: force subagent invocation (isolated context)
---
```

`description` is the only required field. When `agent` references a subagent, subtask invocation
happens automatically. Set `subtask: true` explicitly when you want isolation with a primary agent.
Set `subtask: false` to disable automatic subtask for subagent references.

### Template Body

Everything after frontmatter is the prompt template. Supports:

- **`$ARGUMENTS`**: All arguments as a single string
- **`$1`, `$2`, `$3`...**: Positional arguments
- **`` !`command` ``**: Inject shell output into the prompt
- **`@path/to/file`**: Include file contents

## Writing Effective Commands

### The Five Elements

- **Role/Goal**: what the command is doing; opening directive and domain framing.
- **Expertise**: what it knows; specific tools, patterns, and skill references.
- **Process**: how it works; numbered phases and decision criteria.
- **Output**: what it produces; format templates and required sections.
- **Constraints**: what it will not do; rules, anti-patterns, and stop points.

Simple commands may only need Role/Goal and Constraints. Complex commands benefit from all five.

### Structure Pattern

```markdown
---
description: One-line purpose
---

[Opening directive in imperative mood]

Arguments: $ARGUMENTS

## Process

### 1. [First Phase]
[Steps with specific tool calls, verification, decision points]

### 2. [Next Phase]
[Steps...]

## Output
[Expected deliverable format]

## Rules
[Hard constraints, anti-patterns, stop conditions]
```

Not every command needs all sections. A 3-line command is fine for simple tasks.

### Prompt Engineering Principles

- **Complete but concise.** Include what the agent needs; omit everything else.
- **Specific.** "Run `npm test`, parse failures, correlate with `git blame`" not "analyze
  carefully."
- **Front-load the directive.** State purpose first; models attend most to beginning and end.

### Context Pollution Awareness

Every command runs in the main context window by default. Commands generating large output SHOULD
use `subtask: true` or delegate to a subagent.

### Argument Handling

State fallback behavior explicitly: `Review $ARGUMENTS (or infer from recent discussion if not
provided).`

### Shell Output Injection

Use `` !`command` `` for dynamic context. Commands run in the project root. Bound output size.

```markdown
Current branch status:
!`git status --short`

Based on these changes, prepare a commit message.
```

### Referencing Skills and Files

Reference skills by name; do not duplicate. Use `@path/to/file` to include file contents.

## Command Categories

- **Operational**: short, focused, minimal process. Example: format staged files and report the
  diff.
- **Workflow**: multi-step with phases. Example: generate release notes from git log.
- **Orchestration**: coordinates parallel subagents. Example: validate all open Renovate PRs.
- **Research**: gathers information without mutations. Example: analyze a library upgrade path.

Research and orchestration commands are good candidates for `subtask: true`.

Workflow example:

```markdown
---
description: Prepare release notes
---

Generate release notes for $ARGUMENTS (version tag or range).

### 1. Gather
!`git log --oneline $1`

### 2. Categorize
Group by: breaking changes, features, fixes, chores.

### 3. Output
Markdown release notes with categories and PR references.
```

## Personas

Useful for specialist tasks (security audit, architecture review) and adversarial perspectives.
Establish in the opening line with specific expertise: `You are a senior application security
engineer. You think like an attacker.` Anti-pattern: "You are a helpful AI assistant."

## Validation Checklist

- [ ] Frontmatter has `description` field
- [ ] Description is concise (shown in TUI autocomplete)
- [ ] Opening directive is clear and specific
- [ ] Arguments are documented or fallback behavior stated
- [ ] Shell injections (`` !`cmd` ``) produce bounded output
- [ ] Skills referenced by name (not duplicated)
- [ ] Commands with large output use `subtask: true` or subagent delegation
- [ ] Constraints section present for non-trivial commands
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
- [ ] Command belongs as a command (not AGENTS.md, skill, or subagent)
