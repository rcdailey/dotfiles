---
name: agents-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing AGENTS.md files at any level (repo,
  package, or global); adding, revising, or scoping agent directives, rules, constraints, or
  permissions; converting prose guidance into RFC 2119 rule format; auditing AGENTS.md for
  redundancy, unscoped delegation, or subagent leakage. Triggers on phrases like "update
  AGENTS.md", "add a rule to AGENTS.md", "global directives", or any edit to a file named
  AGENTS.md (including chezmoi source forms).
---

# AGENTS.md Authoring

Conventions for writing AGENTS.md files. Omissions are intentional.

## Core Concept

AGENTS.md is a "README for agents": a dedicated, predictable place for AI coding agent context.
Supported by OpenAI Codex, Google Jules, Cursor, VS Code, GitHub Copilot, Devin, Windsurf, OpenCode,
Aider, and others.

## Writing Style

When writing AGENTS.md content, prefer dense prose over multi-header structures. Collapse related
constraints into single paragraphs. Use bullet lists only for genuine enumeration, not as a
structural default. The screenshot test: if removing a header and merging its content into the
preceding section loses nothing, the header was unnecessary.

## Essential Sections

Every AGENTS.md should cover these areas (not necessarily as separate sections):

1. **Constraints** (dos/don'ts): Be nitpicky. Clear guidelines prevent repeated mistakes.
2. **Commands**: Prefer file-scoped over project-wide. Faster feedback, fewer wasted cycles.
3. **Permissions**: Explicit allow/ask lists prevent surprises.
4. **Structure hints**: A tiny index saves exploration time every session.
5. **Example pointers**: Point to real files. Examples beat abstractions.
6. **When stuck**: Escape hatch for uncertainty.
7. **PR/commit checklist**: Define "ready" explicitly.

Annotated example covering all sections:

````markdown
## Do
- use TypeScript strict mode
- default to small, focused diffs

## Don't
- do not hard code colors; use design tokens
- do not add dependencies without approval

## Commands
# Type check single file (prefer over full build)
npm run tsc --noEmit path/to/file.tsx
# Lint single file
npm run eslint --fix path/to/file.tsx

## Permissions
Allowed without asking: read files, type check, lint, run single unit tests.
Ask first: package installs, git push, deleting files, full build.

## Structure
- routes: `src/App.tsx`
- components: `src/components/`
- design tokens: `src/lib/theme/tokens.ts`

## Examples
Copy: `src/components/UserForm.tsx` (forms), `src/hooks/useProjects.ts` (data fetching).
Avoid: `src/legacy/Admin.tsx` (class component, legacy).

## When stuck
Ask a clarifying question, propose a short plan, or open a draft PR with notes.
Do not push large speculative changes.

## PR checklist
- lint, type check, tests: all green
- diff is small and focused
- brief summary of what changed and why
````

## Alternative: Instructions in opencode.json

Rules can also load via the `instructions` field in `opencode.json`. Supports globs and remote URLs.
All instruction files combine with AGENTS.md content.

```json
{
  "instructions": [
    "CONTRIBUTING.md",
    "packages/*/AGENTS.md",
    "https://raw.githubusercontent.com/my-org/shared-rules/main/style.md"
  ]
}
```

## Nested AGENTS.md for Monorepos

Place AGENTS.md in subdirectories for package-specific rules. OpenCode traverses up from the working
directory to the git worktree root, loading AGENTS.md files it finds. Closer files take precedence.
Global rules in `~/.config/opencode/AGENTS.md` apply across all sessions.

## Context Engineering Principles

**Position sensitivity**: Models attend more to the beginning and end of context. Place critical
rules (safety, correctness, non-negotiable constraints) at the top. Checklists work well at the end.

**Completeness without bloat**: Include what the agent needs to act without guessing. Write
concisely: terse rules, compressed examples, no filler. Remove duplication, but keep reference
material the agent needs. Organize into distinct sections with consistent formatting.

## Rule Writing

Use RFC 2119 keywords (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY) for directives. LLMs parse these as
strict requirement levels, producing measurably higher compliance than softer phrasing.

- `MUST` / `SHALL`: absolute requirement
- `MUST NOT` / `SHALL NOT`: absolute prohibition
- `SHOULD` / `SHOULD NOT`: strong preference; exceptions require justification
- `MAY`: truly discretionary; usually omit instead

**Format: constraint + consequence.** Bad: "Don't commit to main." Good: "MUST NOT commit directly
to main; use feature branches and PRs."

**Prefer positive framing.** Bad: "MUST NOT use var." Good: "MUST use `const` by default, `let` when
reassignment needed (NEVER `var`)."

**Be specific.** Bad: "Be careful with error handling." Good: "All async functions MUST have
try/catch; unhandled rejections crash the process."

**Examples over adjectives.** Bad: "Write concise commit messages." Good: "Format: `fix(auth):
handle expired tokens`."

## Antipatterns

- Repeated rules across files: use a single authoritative location.
- Vague adjectives: replace with concrete criteria or examples.
- Prohibitions without alternatives: include the correct approach.
- Project-wide commands only: prefer file-scoped commands.
- Stripped reference material: include the references the agent needs.
- Verbose explanations: use a terse rule plus one example.
- Multi-header structures for simple related constraints: use one dense paragraph.
- Restating structural enforcement: if a tool or action is denied via permissions or config, do not
  add a prose rule prohibiting it. Positive instructions ("use X") are sufficient; negative
  instructions ("do not use Y") for structurally unavailable capabilities waste tokens.
- Duplicated routing: when a subagent replaces direct tool usage, document the routing in one
  location only. The Agents section is authoritative for delegation rules; do not duplicate routing
  instructions in the Tools section.
- Unscoped delegation: AGENTS.md is inherited by all agents (primary and subagents) with no
  filtering. Delegation directives ("use subagent X for task Y") must scope to primary agents when
  subagents have direct access to the same tools. Otherwise subagents receive conflicting
  instructions: a directive to delegate to an agent they cannot invoke.

## Maintenance

Update AGENTS.md when constraints, tooling, command syntax, or project structure changes. Update the
authoritative location (not duplicates), verify no contradictions, validate formatting.

## Validation Checklist

- [ ] Each constraint has a consequence
- [ ] Commands are copy-pasteable and file-scoped where possible
- [ ] Examples reference real files (not invented)
- [ ] "When stuck" guidance included
- [ ] Line length <= 100 characters
- [ ] Code blocks have language specifiers
