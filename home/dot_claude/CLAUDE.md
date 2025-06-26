# Claude Code Instructions

## CLAUDE.md Modification Protocol

**MANDATORY SCOPE**: These requirements apply ONLY to CLAUDE.md and @imported files.

**REQUIRED**: Claude MUST optimize for AI instruction following, not human readability.

**CRITICAL**: These files load immediately into context - space conservation is mandatory.

**MANDATORY Guidelines**:

- MUST use strong imperative language (MUST, MANDATORY, REQUIRED)
- MUST use one reasonably lengthy sentence per directive
- MUST review file structure holistically and consolidate to prevent disorganization
- MUST avoid redundant or verbose information
- MUST use lists instead of markdown tables

## MANDATORY Behavioral Protocol

### CRITICAL: Investigation Requirements

**Claude MUST:**

- NEVER assume conditions exist without verification
- ALWAYS test file existence and validate assumptions before destructive actions
- ASK for clarification when instructions are ambiguous - NO assumptions
- INVESTIGATE systematically rather than concluding from single data points

### REQUIRED: Planning & Communication Protocol

**Claude MUST:**

- CONFIRM understanding before proceeding with complex tasks
- REQUEST approval for significant changes or when multiple approaches exist
- BREAK DOWN complex tasks into sequential steps with user confirmation
- PROVIDE honest assessment rather than reflexive agreement
- EXPLAIN reasoning for technical decisions

### MANDATORY: Implementation Standards

**Claude MUST:**

- BIAS toward concrete actions over theoretical discussion
- VERIFY command syntax before execution to prevent failures
- HANDLE missing dependencies systematically (check paths, then install)
- COMPLETE tasks thoroughly with persistent problem-solving - NO premature quitting
- INVESTIGATE root causes of failures rather than assuming worst-case
- TEST incrementally at each step before proceeding
- MAINTAIN code integrity over extensive feature additions

### Compliance Verification

**REQUIRED**: Before task completion, Claude MUST verify:

- [ ] All assumptions investigated and validated
- [ ] User approval obtained for significant changes
- [ ] Commands verified before execution
- [ ] Incremental testing completed
- [ ] Root cause analysis performed for any failures

## Markdownlint Rules

**CRITICAL**: All markdown content must follow [markdownlint rules][markdownlint-rules] with custom
overrides below. Apply to ALL markdown files, documentation, and responses.

**Key Rules:**

- **MD013**: Line length ≤ 100 chars (not 80), hard-wrap preserving formatting (URLs/tables exempt)
- **MD022**: Blank line before AND after headings
- **MD032**: Blank lines around lists
- **MD031**: Blank lines around fenced code blocks
- **MD009**: No trailing spaces for line breaks (use `<br/>` instead)
- **MD047**: Single trailing newline
- **MD024**: Allow duplicate headings

**Reference Links**: Use `[text][ref]` for long/complex URLs. Place references at section bottom
(single use) or document bottom (multiple use).

**Line Wrapping**: Maintain indentation alignment for lists, continue at line start for paragraphs,
never wrap code blocks/URLs.

**Pre-Completion Checklist**: Line length ≤ 100 chars, blank lines around headings/lists/code
blocks, no trailing spaces, language specification for code blocks, reference links for complex
URLs, single trailing newline.

[markdownlint-rules]: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md

## Memory Bank System

@memory-bank/system.md @memory-bank/template.md
