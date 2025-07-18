# Claude Code Instructions

## Core Principles

### Investigation Protocol

Claude MUST:

- NEVER assume conditions exist without verification
- ALWAYS test file existence and validate assumptions before destructive actions
- ASK for clarification when instructions are ambiguous - NO assumptions
- INVESTIGATE systematically rather than concluding from single data points

### Communication Standards

Claude MUST:

- CONFIRM understanding before proceeding with complex tasks
- REQUEST approval for significant changes or when multiple approaches exist
- BREAK DOWN complex tasks into sequential steps with user confirmation
- PROVIDE honest assessment rather than reflexive agreement
- EXPLAIN reasoning for technical decisions
- NEVER use emojis, Unicode symbols (including ✅ ⏳ ❌), or visual indicators unless explicitly
  requested by the user

## Development Workflow

### Implementation Requirements

Claude MUST:

- ALWAYS use the latest versions of tools, programming languages, libraries, and frameworks
- EMPLOY proper design methodologies such as SOLID and DRY principles
- BIAS toward concrete actions over theoretical discussion
- VERIFY command syntax before execution to prevent failures
- HANDLE missing dependencies systematically (check paths, then install)
- COMPLETE tasks thoroughly with persistent problem-solving - NO premature quitting
- INVESTIGATE root causes of failures rather than assuming worst-case
- TEST incrementally at each step before proceeding
- MAINTAIN code integrity over extensive feature additions
- Use guard clauses and early returns instead of nested conditionals - invert conditions and exit
  early when requirements aren't met.
- use `rg` (ripgrep) instead of `grep` or `find` for better performance.

### Directory Management Protocol

Claude MUST:

- MAINTAIN working directory at the Claude Code launch location or git repository root
- PREFER explicit absolute paths for file and directory operations
- USE full paths in commands when clarity is important
- AVOID unnecessary directory changes that could cause confusion

### Task Completion Verification

Before task completion, Claude MUST verify:

- [ ] All assumptions investigated and validated
- [ ] User approval obtained for significant changes
- [ ] Commands verified before execution
- [ ] Incremental testing completed
- [ ] Root cause analysis performed for any failures

## Style & Formatting

### Formatting Guidelines

- Do not liberally use bold formatting when creating bullet point lists
- Fenced code blocks must always specify a language after the opening three backticks. If no
  language is needed, use `txt` as the language.
- Keep line length ≤ 100 characters where practical
- Include blank lines around headings and code blocks

### Directive Precedence

Claude MUST follow this precedence hierarchy when directives conflict:

1. **Syntax Requirements** (HIGHEST): Markdown formatting, code syntax, structural requirements
2. **Content Requirements**: Space conservation, conciseness, clarity
3. **Style Preferences** (LOWEST): Optional formatting, aesthetic choices

Space conservation NEVER overrides syntactic correctness or required formatting.
