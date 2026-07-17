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

## Shell Search

MUST use `rg` (ripgrep) over `grep`. MUST use `rg --files -g` over `find -name`. Both are enforced
by tool guards that reject the blocked commands.

ripgrep is recursive by default. `-r` means `--replace`, not recursive. MUST NOT use `-r` or `-rl`
when intending recursive search (it silently replaces matched text in output). Common patterns:

```sh
rg "pattern" path/              # recursive content search (default)
rg -n "pattern" path/           # with line numbers
rg -l "pattern" path/           # files containing matches
rg -c "pattern" path/           # match count per file
rg --files -g "*.yaml" path/    # find files by glob (replaces find -name)
rg -g "*.py" "pattern" path/    # search within file type
```

## Agents

- Subagents MUST use their designated tools (`research scout`, etc.) for repo exploration; MUST NOT
  clone repos or use local file tools on external repositories.
- Citations MUST be literal URLs fetched in the current session (via webfetch or a subagent's
  designated fetch tool). No bracket indices, no placeholder references, no carry-forward from prior
  turns or prior searches. If a URL was not fetched this session, the citation does not exist and
  MUST be omitted. A missing citation beats an unverified one.
