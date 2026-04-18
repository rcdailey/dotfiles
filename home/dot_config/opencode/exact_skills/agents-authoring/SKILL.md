---
name: agents-authoring
description: >-
  Use when creating, editing, refactoring, or reviewing AGENTS.md files at any level (repo,
  package, or global). Triggers on phrases like "update AGENTS.md", "add a rule to AGENTS.md",
  "global directives", or any edit to a file named AGENTS.md (including chezmoi source forms).
  Do NOT use for SKILL.md, agent definitions, or slash commands.
---

# AGENTS.md Authoring

Conventions for AGENTS.md files. Omissions intentional.

## Core Concept

AGENTS.md is a "README for agents": a predictable place for AI coding agent context. Supported by
OpenAI Codex, Google Jules, Cursor, VS Code, GitHub Copilot, Devin, Windsurf, OpenCode, Aider, and
others.

## Writing Style

Prefer dense prose over multi-header structures. Collapse related constraints into single
paragraphs. Use bullet lists only for genuine enumeration. Screenshot test: if removing a header and
merging its content into the preceding section loses nothing, the header was unnecessary.

## Essential Sections

Cover these areas (not necessarily as separate sections):

1. **Constraints** (dos/don'ts): Be nitpicky; clear guidelines prevent repeated mistakes.
2. **Commands**: File-scoped over project-wide; faster feedback.
3. **Permissions**: Explicit allow/ask lists prevent surprises.
4. **Structure hints**: A tiny index saves exploration time.
5. **Example pointers**: Real files beat abstractions.
6. **When stuck**: Escape hatch for uncertainty.
7. **PR/commit checklist**: Define "ready" explicitly.

Compressed example:

````markdown
## Do
- use TypeScript strict mode
- default to small, focused diffs

## Don't
- no hard-coded colors; use design tokens
- no new dependencies without approval

## Commands
npm run tsc --noEmit path/to/file.tsx    # type check single file
npm run eslint --fix path/to/file.tsx    # lint single file

## Permissions
Allowed: read, type check, lint, single unit tests. Ask first: installs, push, deletes, full build.

## Structure
- routes: `src/App.tsx`
- components: `src/components/`
- design tokens: `src/lib/theme/tokens.ts`

## Examples
Copy: `src/components/UserForm.tsx` (forms). Avoid: `src/legacy/Admin.tsx` (class component).

## When stuck
Ask a clarifying question, propose a plan, or open a draft PR. Do not push speculative changes.

## PR checklist
lint + type check + tests green; diff small and focused; summary of what and why.
````

## Skill Routing

Per-skill imperative triggers in AGENTS.md MUST use RFC 2119 keywords. Empirical testing shows
skills relying on frontmatter alone trigger roughly half as often as skills with reinforcing
AGENTS.md directives; softer phrasing produces measurably weaker compliance than MUST.

- Skills used by both primary agents and subagents MUST live in `AGENTS.md`.
- Skills used only by primary agents MUST live in `opencode-primary-shared.md` to avoid subagent
  context bloat.
- The generic "check skills before acting" directive MUST NOT be duplicated across AGENTS.md and
  primary-shared; keep in AGENTS.md only.

## Alternative: Instructions in opencode.json

Rules can load via the `instructions` field (globs + remote URLs); combines with AGENTS.md.

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
directory to the git worktree root; closer files take precedence. Global rules in
`~/.config/opencode/AGENTS.md` apply across all sessions.

## Context Engineering

**Position sensitivity**: Models attend more to the beginning and end of context. Place critical
rules at the top; checklists work at the end.

**Completeness without bloat**: Include what the agent needs to act without guessing. Terse rules,
compressed examples, no filler. Consistent formatting across sections.

## Rule Writing

Use RFC 2119 keywords (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY). LLMs parse these as strict
requirement levels, producing measurably higher compliance than softer phrasing.

- `MUST` / `SHALL`: absolute requirement
- `MUST NOT` / `SHALL NOT`: absolute prohibition
- `SHOULD` / `SHOULD NOT`: strong preference; exceptions require justification
- `MAY`: truly discretionary; usually omit instead

**Constraint + consequence.** Bad: "Don't commit to main." Good: "MUST NOT commit directly to main;
use feature branches and PRs."

**Positive framing.** Bad: "MUST NOT use var." Good: "MUST use `const` by default, `let` when
reassignment needed (NEVER `var`)."

**Specific.** Bad: "Be careful with error handling." Good: "All async functions MUST have try/catch;
unhandled rejections crash the process."

**Examples over adjectives.** Bad: "Write concise commit messages." Good: "Format: `fix(auth):
handle expired tokens`."

## Antipatterns

- Repeated rules across files: single authoritative location.
- Vague adjectives: replace with concrete criteria or examples.
- Prohibitions without alternatives: include the correct approach.
- Verbose explanations: terse rule plus one example.
- Multi-header structures for simple related constraints: one dense paragraph.
- Restating structural enforcement: if denied via permissions, skip the prose rule. Positive
  instructions ("use X") suffice.
- Duplicated routing: document delegation in one location. The Agents section is authoritative for
  delegation; do not duplicate in the Tools section.
- Unscoped delegation: AGENTS.md is inherited by ALL agents with no filtering. Delegation directives
  ("use subagent X") MUST scope to primary agents when subagents have direct access to the same
  tools; otherwise subagents receive directives to delegate to agents they cannot invoke.

## Validation Checklist

- [ ] Each constraint has a consequence
- [ ] Commands copy-pasteable; file-scoped where possible
- [ ] Examples reference real files
- [ ] "When stuck" guidance included
- [ ] Skill routing directives use RFC 2119 keywords
- [ ] Skill routing scoped correctly (primary-only skills in primary-shared)
