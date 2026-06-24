# Global Directives

## Core Rules

- Act, don't ask. When a request leaves minor details unspecified, make a reasonable attempt now
  rather than interviewing the user first. Use tools to discover missing details rather than
  guessing or asking. Only ask upfront when the request is genuinely unanswerable without the
  missing information.
- Don't provide time estimates.

## Skills

MUST check the available skills list before any task. MUST load a matching skill BEFORE acting on
the governed task; skills loaded in parallel with that action arrive too late. MUST load skills
alone (never in parallel with other tool calls).

Per-skill triggers:

- `agents-authoring`: MUST load when creating, editing, or reviewing AGENTS.md files.
- `skill-authoring`: MUST load when creating, editing, or reviewing SKILL.md files.
- `subagent-authoring`: MUST load when creating, editing, or refactoring agent definitions.
- `command-authoring`: MUST load when creating, editing, or refactoring OpenCode slash commands.
- `git-hunks`: MUST load when staging individual hunks or partial file changes non-interactively.
- `python-scripting`: MUST load when creating, editing, or reviewing modularized Python CLI script
  projects (uv + hatchling + Click pattern).

## Agents

- Subagents MUST use their designated tools (`research scout`, etc.) for repo exploration; MUST NOT
  clone repos or use local file tools on external repositories.
- Citations MUST be literal URLs fetched in the current session (via webfetch or a subagent's
  designated fetch tool). No bracket indices, no placeholder references, no carry-forward from prior
  turns or prior searches. If a URL was not fetched this session, the citation does not exist and
  MUST be omitted. A missing citation beats an unverified one.
