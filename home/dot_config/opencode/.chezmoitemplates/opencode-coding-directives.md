## General

- Fenced code blocks require a language specifier (use `txt` if none applies).
- Keep code and authored file content <= 100 chars per line; this limit does not apply to chat.
- Use blank lines around headings and code blocks.

## Development

- Use latest stable versions of tools, languages, libraries, frameworks.
- Prefer idiomatic patterns: use framework-native solutions over hand-rolled equivalents, current
  API surfaces over deprecated predecessors, and official usage recommendations over ad-hoc
  approaches.
- Reduce nesting: invert conditions, exit early.
- YAML: don't quote values unless required for disambiguation.
- Prefer defaults by omission over explicit configuration.
- Comments must earn their place by reducing cognitive load. Prefer self-documenting naming.
- Match existing codebase patterns rather than introducing new ones. When inconsistencies exist,
  unify them rather than adding a third approach.
- MUST NOT use the 'write' tool on an existing file; use 'edit' tools for surgical edits. Full-file
  rewrites waste tokens and risk clobbering unseen content.
- For current library or framework APIs, MUST use `ctx7` first. Run `ctx7 library <name> <query>` to
  resolve a library ID, then `ctx7 docs <library-id> <query>` for the relevant API. Use official
  sources when Context7 lacks coverage.
- Keep PR descriptions high-level, focused on the change. Skip test plans and template boilerplate.
- Prefer structured output (JSON + jq) over table/text for CLI tools that support it (aws, gh,
  kubectl, docker). Structured output is parseable, filterable, and scriptable.

## Git

- When creating local branches, MUST NOT set a tracking branch initially (`git checkout -b` or `git
  branch` without `-t`/`--track`). Tracking is set later via `git push -u`.
- For UD/DU conflicts (file deleted on one side, modified on the other), MUST NOT blindly accept the
  deletion. Run `git diff REBASE_HEAD...HEAD -- <file>` to see the upstream modifications being
  discarded, then port any meaningful changes to the replacement files before resolving with `git
rm`.

## Architecture

Apply KISS, DRY, SOLID, and YAGNI pragmatically.

- Prefer the simplest coherent design that meets current requirements. Refactor affected code when
  that removes duplication, special cases, or accumulated indirection; do not add abstractions,
  configurability, or extensibility for hypothetical future needs.
- Collapse indirection layers that delegate without adding value.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n\*m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Tools

- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use LSP for symbol definitions, references, types, implementations, and call graphs. Use glob and
  grep for file and text discovery.
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for PDF files: `pdf2md <file-or-url>`. Run `pdf2md --help` for full usage.
- The Glob tool skips dot-directories (`.github/`, `.vscode/`, etc.). For those, use bash: `rg
--files --hidden -g "pattern" --glob '!**/.git/**'`.

## Skills

- `agents-authoring`: MUST load when creating, editing, or reviewing AGENTS.md files.
- `skill-authoring`: MUST load when creating, editing, or reviewing SKILL.md files.
- `subagent-authoring`: MUST load when creating, editing, refactoring, or reviewing agent
  definitions.
- `command-authoring`: MUST load when creating, editing, refactoring, or reviewing OpenCode slash
  commands.
- `python-scripting`: MUST load when creating, editing, or reviewing modularized Python CLI script
  projects (uv + hatchling + Click pattern).
