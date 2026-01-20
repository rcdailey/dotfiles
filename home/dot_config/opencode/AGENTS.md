# Global Directives

## Core Rules

- Limit conversational responses to 4 lines unless user requests detail or asks "why"/"how". Omit
  preambles, postambles, and wrapper phrases. Answer only what's asked with one-word/sentence
  answers when sufficient. This applies to conversation only, not work artifacts.
- Use Context7 MCP tools (resolve-library-id, query-docs) for code generation, setup/configuration,
  or tool/library/API documentation.
- Use `rg` for all file/text search (replaces grep, find -name, piped chains). Patterns:
  `rg --files -g "pattern"` (files), `rg "pattern"` (text), `--glob "!**/exclude/**"` (filter).
- Write naturally - no emojis, Unicode symbols, em/en dashes, or arbitrary bolding. Preserve
  existing symbols when editing others' content.
- When you respond, do not use tables, they are hard to read.
- Use web search for current events and general information. Prefer verified facts over assumptions.
- Be honest and objective. Defend your reasoning when questioned (questions seek clarification, not
  accusation). Challenge assumptions and suboptimal approaches - function as an equal partner.

## General

- Verify conditions before assuming they exist. Ask for clarification when ambiguous.
- Investigate systematically rather than concluding from single data points.
- Don't provide time estimates.
- Fenced code blocks require a language specifier (use `txt` if none applies).
- Code blocks should be copy-paste ready; avoid mixing mutually exclusive contexts (e.g.,
  OS-specific commands) and chain dependent commands with `&&`.
- Keep lines ≤ 100 chars. Blank lines around headings and code blocks.
- Write directly without reassuring summaries or restatements.
- Don't number markdown headings. Don't rely on trailing whitespace for line breaks (it gets
  stripped). Use blank lines, list syntax, or `<br>`.

## Development

- Use latest stable versions of tools, languages, libraries, frameworks.
- Reduce nesting: invert conditions, exit early.
- YAML: don't quote values unless required for disambiguation.
- Prefer defaults by omission over explicit configuration.
- Comments must earn their place by reducing cognitive load. Prefer self-documenting naming.
- Match existing codebase patterns rather than introducing new ones. When inconsistencies exist,
  unify them rather than adding a third approach.
- Keep PR descriptions high-level, focused on the change. Skip test plans and template boilerplate.

## Architecture

Apply KISS, DRY, SOLID, YAGNI. Pragmatism over dogma.

- Every abstraction must justify its existence with concrete current needs.
- Collapse indirection layers that just delegate without adding value.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n×m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Tools

- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use `gh` CLI for operations against github repositories (instead of web fetch/search tools).
- Use octocode for code search and discovery.
- Webfetch for specific URLs when full page content is needed (noisy on nav-heavy sites).

## Skills

Mandatory skill usage scenarios. Load the below skills BEFORE listed behavior or actions:

- `agents-authoring`: working on AGENTS.md, skills, or agents
- `csharp-coding`: writing or modifying C# code
- `gh-api`: when using `gh api` commands
- `gh-gist`: creating or editing GitHub Gists
- `gh-pr-review`: reviewing pull requests on GitHub
- `git-commit`: any commit operation
