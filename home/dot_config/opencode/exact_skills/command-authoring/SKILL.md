---
name: command-authoring
description: >-
  Use when creating, editing, or refactoring OpenCode custom commands
  (slash commands in .opencode/commands/ or ~/.config/opencode/commands/)
---

# Command Authoring

Conventions and patterns for OpenCode custom commands. Omissions are intentional.

## Command Anatomy

### File Location

- **Global**: `~/.config/opencode/commands/<name>.md`
- **Per-project**: `.opencode/commands/<name>.md`

The filename (without `.md`) becomes the `/command-name`.

### Required Frontmatter

```yaml
---
description: Brief description shown in TUI autocomplete
---
```

`description` is the only required field. It appears in the TUI when the user types `/`.

### Optional Frontmatter

| Field     | Type    | Purpose                                      |
| --------- | ------- | -------------------------------------------- |
| `agent`   | string  | Which agent executes (defaults to current)   |
| `model`   | string  | Override the default model                   |
| `subtask` | boolean | Force subagent invocation (isolated context) |

```yaml
---
description: Deep code review with fresh context
agent: plan
subtask: true
---
```

When `agent` references a subagent, subtask invocation happens automatically. Set `subtask: true`
explicitly when you want isolation even with a primary agent (keeps main context clean). Set
`subtask: false` to disable automatic subtask for subagent references.

### Template Body

Everything after the frontmatter is the prompt template. Supports:

- **`$ARGUMENTS`**: All arguments as a single string
- **`$1`, `$2`, `$3`...**: Positional arguments
- **`` !`command` ``**: Inject shell output into the prompt
- **`@path/to/file`**: Include file contents

## Writing Effective Commands

### Structure Pattern

Well-structured commands follow this skeleton:

```markdown
---
description: One-line purpose
---

[Opening directive: what the agent should do, in imperative mood]

Arguments: $ARGUMENTS (or describe what $1, $2, etc. mean)

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

### The Five Elements

Effective commands share five elements:

| Element         | Question             | How It Manifests                           |
| --------------- | -------------------- | ------------------------------------------ |
| **Role/Goal**   | What are you doing?  | Opening directive, domain framing          |
| **Expertise**   | What do you know?    | Specific tools, patterns, skill references |
| **Process**     | How do you work?     | Numbered phases, decision criteria         |
| **Output**      | What do you produce? | Format templates, required sections        |
| **Constraints** | What won't you do?   | Rules section, anti-patterns, stop points  |

Simple commands may only need Role/Goal and Constraints. Complex commands benefit from all five.

### Prompt Engineering Principles

**Present a complete world.** The command template is the agent's entire understanding of the task.
Include everything needed to act correctly. If the command uses a custom tool or skill, reference it
by name; do not assume the agent will discover it.

**Be specific, not vague.** "Analyze the code carefully" is useless. "Run `npm test`, parse
failures, correlate with `git blame`" is actionable.

**Constraints over examples.** Telling the agent what NOT to do is safe and effective. Examples risk
overfitting (the agent pattern-matches too literally). When examples are necessary, one excellent
example beats three mediocre ones.

**Front-load the directive.** Models pay most attention to the beginning and end of the prompt.
State what the command does in the first sentence.

**Consistency across components.** If the command references a tool, file path, or skill, ensure
those references are accurate. Do not surprise the model with mismatched expectations.

### Context Pollution Awareness

Every command runs in the main context window by default. Long outputs (test results, logs, large
diffs) accumulate and degrade performance. Subagent isolation can yield ~8x cleaner main context for
diagnostic tasks compared to inline slash commands.

**Guidelines:**

- Commands that generate large output (test runners, log analyzers, multi-file research) SHOULD use
  `subtask: true` or delegate to a subagent
- Commands that produce concise, actionable output (commit prep, code generation, quick analysis)
  work fine in the main context
- If a command runs shell commands that produce verbose output, consider having it summarize rather
  than dumping raw output

### Argument Handling

```markdown
# Full arguments string
Analyze $ARGUMENTS for security vulnerabilities.

# Positional arguments
Create a $1 component in $2 with these features: $3

# Optional arguments with fallback
Review $ARGUMENTS (or infer from recent discussion if not provided).
```

Design commands so they degrade gracefully when arguments are missing. State the fallback behavior
explicitly.

### Shell Output Injection

Use `` !`command` `` to include live data in the prompt:

```markdown
Current branch status:
!`git status --short`

Based on these changes, prepare a commit message.
```

Commands run in the project root. Use this for dynamic context the agent needs before acting. Do not
use it for commands with massive output (pipe through `head` or summarize instead).

### Referencing Skills

Commands can (and should) reference skills when the command enters a domain covered by an existing
skill:

```markdown
Load the `gh-pr-review` skill for review etiquette and tooling reference.
```

This tells the agent to load the skill for procedural knowledge, while the command provides the
task-specific workflow. Avoid duplicating skill content in the command.

### Referencing Files

Use `@path/to/file` to include file contents:

```markdown
Review the component in @src/components/Button.tsx.
Check for accessibility issues.
```

The file content is injected into the prompt automatically.

## Personas in Commands

Giving the agent a specific role identity can improve output quality when used correctly, but it is
not universally necessary.

### When Personas Help

- **Specialist tasks** where domain framing improves output: security audit, performance review,
  architecture analysis
- **Adversarial perspective** where the agent should challenge assumptions: devil's advocate, risk
  analysis
- **Consistent output format** where the persona anchors behavior across invocations

### When Personas Are Unnecessary

- Simple operational tasks (run tests, format files, generate boilerplate)
- Tasks where the directive is already specific enough
- Commands that delegate to subagents (the subagent's own prompt handles persona)

### Persona Pattern

When using a persona, establish it in the opening line:

```markdown
You are a senior application security engineer specializing in code review.
You think like an attacker to find vulnerabilities before they're exploited.
```

Effective personas include: specific seniority/expertise, a perspective or stance (not just a job
title), and bounded domain knowledge.

**Anti-pattern**: "You are a helpful AI assistant." This says nothing actionable.

## Command Categories

### Operational Commands

Short, focused tasks. Minimal process, clear output.

```markdown
---
description: Format staged files
---

Run the project formatter on all staged files. Report what changed.
Do not commit.
```

### Workflow Commands

Multi-step processes with phases.

```markdown
---
description: Prepare release notes
---

Generate release notes for $ARGUMENTS (version tag or range).

## Process

### 1. Gather Changes
!`git log --oneline $1`

### 2. Categorize
Group by: breaking changes, features, fixes, chores.

### 3. Output
Format as markdown release notes with categories and PR references.
```

### Orchestration Commands

Commands that coordinate subagents for parallel or isolated work. Use for tasks where context
pollution is a concern or parallelism is beneficial.

```markdown
---
description: Validate all open Renovate PRs
---

List open Renovate PRs. Launch one explore subagent per PR in parallel.
Each subagent researches breaking changes and reports back.
Present unified summary.
```

### Research Commands

Commands that gather information without making changes. Good candidates for `subtask: true` to keep
main context clean.

```markdown
---
description: Research library upgrade path
subtask: true
---

Research the upgrade path from current to latest version of $ARGUMENTS.
Check changelogs, migration guides, and breaking changes.
Return a concise summary of required changes.
```

## Common Mistakes

| Mistake                   | Symptom                   | Fix                          |
| ------------------------- | ------------------------- | ---------------------------- |
| Vague directive           | Inconsistent output       | Specific verbs, named tools  |
| Verbose output inline     | Context pollution         | Use subtask or summarize     |
| Duplicating skill content | Drift, maintenance burden | Reference skill by name      |
| No argument fallback      | Fails without args        | State fallback explicitly    |
| Overengineered persona    | Follows persona, not task | Persona is framing, not task |
| Missing constraints       | Unexpected agent behavior | Add Rules section            |
| Too many commands         | Cognitive overhead        | Consolidate; use args        |
| Belongs in AGENTS.md      | Redundant, may conflict   | Move to AGENTS.md            |

## Refactoring Existing Commands

When editing an existing command:

1. **Read the current command** to understand its intent and structure
2. **Check if it should be a command** (vs AGENTS.md rule, skill, or subagent prompt)
3. **Identify context pollution risk**: does it generate large output in-line?
4. **Apply the five elements**: which are missing or vague?
5. **Test mentally**: given this prompt, would the agent produce consistent results?

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
