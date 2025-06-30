# Claude Code Instructions

## File Optimization Protocol

**SCOPE**: These requirements apply ONLY to CLAUDE.md and @imported files.

Claude MUST optimize content density by eliminating verbose explanations, redundant information, and
unnecessary commentary while MAINTAINING all required formatting and structural elements.

### Structure Requirements

When modifying CLAUDE.md or @imported files, Claude MUST:

- USE functional section names without priority markers (Investigation Protocol, Communication
  Standards, Implementation Requirements)
- ORGANIZE content with consistent "Claude MUST:" directive blocks for all behavioral requirements
- ELIMINATE redundant priority markers (MANDATORY/REQUIRED/CRITICAL) that create artificial
  hierarchy
- CONSOLIDATE related directives into single sections to prevent fragmentation
- MAINTAIN one reasonably lengthy sentence per directive for clarity and space efficiency
- REPLACE verbose explanations with direct, actionable instructions
- USE lists instead of markdown tables for better space utilization
- VERIFY compliance with MARKDOWN_RULES during and after content generation
- MAINTAIN all MARKDOWN_RULES requirements throughout modifications

### Language Standards

When modifying CLAUDE.md files, Claude MUST:

- USE imperative verbs (MUST/NEVER/ALWAYS) for behavioral directives
- AVOID mixing priority markers with directive content
- WRITE directives as complete behavioral requirements rather than partial instructions
- ENSURE each directive is independently actionable without requiring interpretation
- NEVER use emojis in text output unless explicitly requested by the user

### Markdown Compliance Verification

After any edit to markdown files, Claude MUST verify compliance with MARKDOWN_RULES before
considering the edit complete.

## Directive Precedence

Claude MUST follow this precedence hierarchy when directives conflict:

1. **Syntax Requirements** (HIGHEST): Markdown formatting, code syntax, structural requirements
2. **Content Requirements**: Space conservation, conciseness, clarity
3. **Style Preferences** (LOWEST): Optional formatting, aesthetic choices

Space conservation NEVER overrides syntactic correctness or required formatting.

## Investigation Protocol

Claude MUST:

- NEVER assume conditions exist without verification
- ALWAYS test file existence and validate assumptions before destructive actions
- ASK for clarification when instructions are ambiguous - NO assumptions
- INVESTIGATE systematically rather than concluding from single data points

## Communication Standards

Claude MUST:

- CONFIRM understanding before proceeding with complex tasks
- REQUEST approval for significant changes or when multiple approaches exist
- BREAK DOWN complex tasks into sequential steps with user confirmation
- PROVIDE honest assessment rather than reflexive agreement
- EXPLAIN reasoning for technical decisions

## Implementation Requirements

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

## Task Completion Verification

Before task completion, Claude MUST verify:

- [ ] All assumptions investigated and validated
- [ ] User approval obtained for significant changes
- [ ] Commands verified before execution
- [ ] Incremental testing completed
- [ ] Root cause analysis performed for any failures

## Markdown Formatting Standards

Claude MUST follow ALL rules defined in this section (collectively "MARKDOWN_RULES") - these are
critical system requirements that override content optimization:

**Required Rules:**

- **MD013**: Line length ≤ 100 chars (not 80), hard-wrap preserving formatting (URLs/tables exempt)
- **MD022**: Blank line before AND after headings
- **MD032**: Blank lines around lists
- **MD031**: Blank lines around fenced code blocks
- **MD009**: No trailing spaces for line breaks (use `<br/>` instead)
- **MD047**: Single trailing newline
- **MD024**: Allow duplicate headings

**Reference Links**: Use `[text][ref]` for long/complex URLs, place references at section bottom
(single use) or document bottom (multiple use).

**Line Wrapping**: Maintain indentation alignment for lists, continue at line start for paragraphs,
never wrap code blocks/URLs.

**Completion Requirements**: Line length ≤ 100 chars, blank lines around headings/lists/code blocks,
no trailing spaces, language specification for code blocks, reference links for complex URLs, single
trailing newline.

[markdownlint-rules]: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md

## Memory Bank System

**NOTE**: Files referenced below are user-level configuration automatically imported - NEVER search
for or modify these within project repositories.

@memory-bank/system.md @memory-bank/template.md
