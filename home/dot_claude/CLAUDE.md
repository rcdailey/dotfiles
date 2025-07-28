# Claude Code Global Directives

## General

- NEVER assume conditions exist without verification.
- ASK for clarification when instructions are ambiguous - NO assumptions.
- INVESTIGATE systematically rather than concluding from single data points.
- PROVIDE honest assessment rather than reflexive agreement.
- NEVER provide time estimates for your work; it's confusing and doesn't make sense when an AI is
  doing the work.

## Response & Output Requirements

- NEVER use emojis, Unicode symbols (including ✅ ⏳ ❌), or visual indicators unless explicitly
  requested by the user.
- Do not liberally use bold formatting when creating bullet point lists.
- Fenced code blocks must always specify a language after the opening three backticks. If no
  language is needed, use `txt` as the language.
- Keep line length ≤ 100 characters where practical.
- Include blank lines around headings and code blocks.
- Write directly and concisely without adding reassuring summaries, value justifications, or
  restatements of what you've already explained.

## Development Mandates

- APPLY the KISS principle (Keep It Simple, Stupid) - prioritize simplicity over complexity.
- ALWAYS use the latest stable versions of tools, programming languages, libraries, and frameworks.
- EMPLOY proper design methodologies such as SOLID and DRY principles.
- AVOID high levels of indentation in code: invert if conditions and exit early to reduce nesting.

## Code Quality Requirements

- ALWAYS write self-documenting code and avoid verbose code comments to improve code base
  maintainability. Comments are code, too, and they have a cost.
- ALWAYS analyze existing code conventions and patterns in the project before making changes.

## Tool Usage Requirements

- USE Zsh for all shell operations and script execution - leveraging Zinit plugin manager for
  optimal performance and automation.
- ALWAYS use `#!/usr/bin/env <interpreter>` for script shebangs (e.g., `#!/usr/bin/env zsh`,
  `#!/usr/bin/env python3`, `#!/usr/bin/env bash`) for portability across systems.
- ALWAYS use `rg` (ripgrep) instead of `grep` or `find` for superior performance and capabilities.
- ALWAYS use GitHub MCP tools as the primary method for GitHub operations (e.g. don't use WebFetch
  for github.com) and information retrieval; use GitHub CLI (gh) only as fallback when MCP tools are
  unavailable.

## Configuration Principles

- PREFER default values by omission over explicit configuration - minimal configuration improves
  maintainability and clarity of intent.
