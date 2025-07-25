# Claude Code Global Directives

## General

- NEVER assume conditions exist without verification
- ASK for clarification when instructions are ambiguous - NO assumptions
- INVESTIGATE systematically rather than concluding from single data points
- PROVIDE honest assessment rather than reflexive agreement
- NEVER provide time estimates for your work; it's confusing and doesn't make sense when an AI is
  doing the work.

## Response & Output Requirements

- NEVER use emojis, Unicode symbols (including ✅ ⏳ ❌), or visual indicators unless explicitly
  requested by the user
- Do not liberally use bold formatting when creating bullet point lists
- Fenced code blocks must always specify a language after the opening three backticks. If no
  language is needed, use `txt` as the language.
- Keep line length ≤ 100 characters where practical
- Include blank lines around headings and code blocks

## Development Mandates

- ALWAYS use the latest versions of tools, programming languages, libraries, and frameworks
- EMPLOY proper design methodologies such as SOLID and DRY principles
- AVOID high levels of indentation in code: invert if conditions and exit early to reduce nesting.

## Tool Usage Requirements

- ALWAYS use `rg` (ripgrep) instead of `grep` or `find` for superior performance and capabilities.
- ALWAYS use GitHub MCP tools as the primary method for GitHub operations (e.g. don't use WebFetch
  for github.com) and information retrieval; use GitHub CLI (gh) only as fallback when MCP tools are
  unavailable.
