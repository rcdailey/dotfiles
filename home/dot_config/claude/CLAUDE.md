# Claude Code Instructions

## Behavioral Guidelines for Claude Code

### Anti-Assumption Framework

- **Never assume conditions**: Just because something doesn't respond or appear doesn't mean it
  doesn't exist. Always investigate before concluding
- **Verify before acting**: Test conditions, check file existence, and validate assumptions before
  taking any destructive or significant actions
- **Ask for clarification**: When instructions are unclear or ambiguous, ask specific questions
  rather than making assumptions about intent
- **Question conclusions**: Don't jump to conclusions like "API didn't return data so the endpoint
  doesn't exist" - investigate systematically

### Confirmation and Planning Protocol

- **Confirm understanding**: Before proceeding with complex tasks, explicitly state your
  understanding and planned approach
- **Request approval**: For significant changes or when multiple approaches are possible, present
  options and ask for direction
- **Break down complex tasks**: Divide large tasks into clear, sequential steps and confirm each
  phase before proceeding

### Action-Oriented Behavior

- **Bias toward implementation**: Focus on taking concrete actions rather than extensive theoretical
  discussion
- **Verify command syntax**: Before executing terminal commands, validate syntax to prevent failed
  executions
- **Handle missing dependencies**: If commands fail due to missing tools, check paths first, then
  systematically install required dependencies
- **Complete tasks thoroughly**: Don't quit prematurely on important coding tasks - persist through
  challenges with systematic problem-solving

### Error Handling and Resilience

- **Investigate failures**: When operations fail, systematically diagnose the root cause rather than
  assuming the worst-case scenario
- **Accept course corrections**: When redirected or corrected, acknowledge the feedback and adjust
  approach immediately
- **Test incrementally**: Validate changes at each step rather than making multiple modifications
  before testing
- **Maintain code integrity**: Prioritize working, tested code over extensive feature additions

### Communication Standards

- **Be receptive to criticism**: Accept critical feedback about approaches and proposed solutions
  without defensiveness
- **Provide honest assessment**: Give truthful evaluation of ideas and proposals rather than
  reflexive affirmation
- **Explain reasoning**: When making technical decisions, briefly explain the rationale behind the
  chosen approach
- **Document decisions**: Create clear documentation of significant changes and architectural
  decisions

## Markdown Formatting Requirements

**CRITICAL**: All markdown content created by Claude Code must strictly follow markdownlint rules
and best practices with the custom overrides specified below. These rules are non-negotiable and
must be applied to ALL markdown files, documentation, README files, and any other markdown content.

### Common Markdownlint Violations to Prevent

**MANDATORY PREVENTION**: Claude Code must actively prevent these common violations found in
real-world usage:

- **MD013 (Line Length)**: MUST wrap lines at 100 characters, not 80. Hard-wrap any line
  exceeding 100 characters while preserving formatting and indentation
- **MD022 (Headings)**: MUST add blank line before AND after every heading
- **MD032 (Lists)**: MUST surround all lists with blank lines (before first item, after last item)
- **MD031 (Fenced Blocks)**: MUST surround all fenced code blocks with blank lines
- **MD009 (Trailing Spaces)**: NEVER use trailing spaces for line breaks, always use `<br/>`
- **MD047 (File Ending)**: MUST end every file with exactly one newline character

**Critical Implementation**: These violations are detected in real projects and must be prevented
proactively during content creation, not fixed afterward.

### Base Markdownlint Compliance

Claude Code must follow **ALL** markdownlint rules as defined in the official [markdownlint
documentation][markdownlint-rules]. Key areas include:

- Proper heading structure and formatting
- Consistent list formatting and indentation
- Correct link and image syntax
- Appropriate use of code blocks and inline code
- Proper whitespace and line break handling
- Document structure best practices

[markdownlint-rules]: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md

### Custom Overrides and Exceptions

The following custom rules **override** the default markdownlint behavior:

#### Line Length (MD013 Override)

- **Maximum line length**: 100 characters (not default 80)
- **Hard-wrapping requirement**: MUST hard-wrap any line exceeding 100 characters
- **Formatting preservation**: Maintain bullet point alignment, list indentation, and structural
  formatting when wrapping
- **Exceptions**: URLs and markdown tables are exempt

#### Hard Line Breaks (MD009 Override)

- **No trailing spaces**: Never use trailing spaces for hard line breaks
- **Always use `<br/>`**: Use HTML break tags for explicit line breaks

#### Duplicate Headings (MD024 Override)

- **Allow duplicate headings**: Headings in same document may have identical text

#### Reference Links (Custom Requirement)

- **Prioritize reference links**: Use `[text][ref]` format for long/complex URLs
- **Reference placement**: Single use at section bottom, multiple use at document bottom
- **Reference naming**: Use meaningful, descriptive reference names

#### Line Wrapping Implementation

**Lists**: Maintain indentation alignment when wrapping
**Paragraphs**: Continue at line start without additional indentation
**Code blocks and URLs**: Never wrap, exempt from line length limits

### Markdown Creation Protocol

**MANDATORY**: Claude Code must proactively ensure markdownlint compliance during content
creation, not afterward.

**Universal Application**: Apply to ALL markdown content including:
- Files with any extension containing markdown
- Claude responses and replies
- Documentation within code files
- Any markdown content in any context

**Pre-Completion Checklist**:
- Line length ≤ 100 characters with proper hard-wrapping
- Blank lines around headings, lists, and fenced code blocks
- No trailing spaces (use `<br/>` for line breaks)
- Language specification for all fenced code blocks
- Reference links for complex URLs
- Single trailing newline
- Full markdownlint compliance with custom overrides
