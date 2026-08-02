# Global Directives

## Core Rules

- Act, don't ask. When a request leaves minor details unspecified, make a reasonable attempt now
  rather than interviewing the user first. Use tools to discover missing details rather than
  guessing or asking. Only ask upfront when the request is genuinely unanswerable without the
  missing information.
- Deliver what was asked, at the scope intended. Code you are already changing is in scope for
  cleanup; refactor it rather than letting it degrade. MUST NOT expand into adjacent code, add
  unrequested features, or reframe the task.
- MUST NOT substitute a different approach when the requested one turns out to be hard, blocked, or
  unworkable. Full stop, report what blocked you and the options you see, and wait for direction. A
  change of direction requires explicit approval; this outranks "Act, don't ask", which governs
  unspecified details only. Subagents report `blocked` to their caller instead of asking.
- Match user-facing written artifact length to substance. MUST NOT pad with filler sections,
  redundant summaries, or boilerplate. This rule does not govern prompts sent to subagents.
- Don't provide time estimates.
- MUST NOT use the 'write' tool on an existing file; use 'edit' tools for surgical edits. Full-file
  rewrites waste tokens and risk clobbering unseen content.

## Documentation

- For current library or framework APIs, MUST use `aidocs_search_docs` first. If a library is
  missing, MUST index its official documentation with `aidocs_scrape_docs` before using other
  sources.
- Documentation MCP results are research leads. Fetch a result URL through an allowed fetch tool
  before citing it.

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

ripgrep is recursive by default; no flag enables it. `-r` is `--replace=REPLACEMENT`: it takes an
argument, so `rg -r "pattern" path/` consumes `pattern` as replacement text and searches for `path/`
instead. MUST NOT use `-r` or `-rl` for recursion. Common patterns:

```sh
rg "pattern" path/              # recursive content search (default)
rg -n "pattern" path/           # with line numbers
rg -l "pattern" path/           # files containing matches
rg -c "pattern" path/           # match count per file
rg -i / -w / -F "pattern"       # case-insensitive / whole-word / literal
rg -A3 -B3 "pattern"            # context lines after/before
rg --files -g "*.yaml" path/    # find files by glob (replaces find -name)
rg -g "*.py" "pattern" path/    # restrict search to a glob
rg --hidden -g "!**/.git/**"    # include dot-directories
```

## Agents

- Subagents MUST use their designated tools for repo exploration; MUST NOT clone repos or use local
  file tools on external repositories.
- Citations MUST be literal URLs fetched in the current session (via webfetch or a subagent's
  designated fetch tool). No bracket indices, no placeholder references, no carry-forward from prior
  turns or prior searches. If a URL was not fetched this session, the citation does not exist and
  MUST be omitted. A missing citation beats an unverified one.
