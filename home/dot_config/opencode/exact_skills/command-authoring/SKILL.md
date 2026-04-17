---
name: command-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing OpenCode custom slash commands;
  writing or revising command frontmatter, arguments, agent routing, or permissions;
  converting a recurring workflow into a reusable slash command. Triggers on phrases
  like "new slash command", "add a /command", "edit the command file", or any edit to
  files in a commands directory (including chezmoi source forms).
---

# Command Authoring

Conventions and patterns for OpenCode custom commands. Omissions are intentional.

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

- **Present a complete world, concisely.** The template is the agent's entire understanding. Include
  what it needs (tool names, skill references, constraints) but keep prose tight.
- **Be specific.** "Analyze carefully" is useless. "Run `npm test`, parse failures, correlate with
  `git blame`" is actionable.
- **Constraints over examples.** Examples risk overfitting. When necessary, one excellent example
  beats three mediocre ones.
- **Front-load the directive.** Models attend most to the beginning and end. State purpose first.

### Context Pollution Awareness

Every command runs in the main context window by default. Long outputs accumulate and degrade
performance.

- Commands generating large output (test runners, log analyzers) SHOULD use `subtask: true` or
  delegate to a subagent
- Commands producing concise output (commit prep, quick analysis) work fine inline
- If shell commands produce verbose output, have the command summarize rather than dump raw text

### Argument Handling

Design commands to degrade gracefully when arguments are missing. State fallback behavior
explicitly: `Review $ARGUMENTS (or infer from recent discussion if not provided).`

### Shell Output Injection

Use `` !`command` `` for dynamic context. Commands run in the project root. Avoid commands with
massive output (pipe through `head` or summarize).

```markdown
Current branch status:
!`git status --short`

Based on these changes, prepare a commit message.
```

### Referencing Skills and Files

Reference skills by name when the command enters a covered domain. Avoid duplicating skill content.
Use `@path/to/file` to include file contents in the prompt.

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

Giving the agent a role identity helps for specialist tasks (security audit, architecture review)
and adversarial perspectives (devil's advocate, risk analysis). Unnecessary for simple operational
tasks or when the directive is already specific enough.

When using a persona, establish it in the opening line with specific expertise and a stance: `You
are a senior application security engineer. You think like an attacker.`

Anti-pattern: "You are a helpful AI assistant." (says nothing actionable)

## Common Mistakes

- Vague directive: use specific verbs and named tools.
- Verbose output inline: use `subtask: true` or summarize.
- Duplicating skill content: reference the skill by name.
- No argument fallback: state fallback behavior explicitly.
- Overengineered persona: persona is framing, not the task.
- Missing constraints: add a `Rules` section.
- Too many commands: consolidate and use arguments.
- Belongs in AGENTS.md: move persistent rules to AGENTS.md.

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
