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

### Base Markdownlint Compliance

Claude Code must follow **ALL** markdownlint rules as defined in the official [markdownlint
documentation][markdownlint-rules]. This includes but is not limited to:

- Proper heading structure and formatting
- Consistent list formatting and indentation
- Correct link and image syntax
- Appropriate use of code blocks and inline code
- Proper whitespace and line break handling
- Document structure best practices

The goal is comprehensive compliance with the entire markdownlint ruleset, not just a subset of
rules.

[markdownlint-rules]: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md

### Custom Overrides and Exceptions

The following custom rules **override** the default markdownlint behavior:

#### Line Length (MD013 Override)

- **Maximum line length**: 100 characters
- **Hard-wrapping requirement**: MUST hard-wrap any line that exceeds 100 characters
- **Use maximum space**: Fill lines to near the 100-character limit before wrapping
- **Mandatory wrapping**: When a line reaches or exceeds 100 characters, immediately wrap to the
  next line maintaining proper alignment and indentation
- **Formatting preservation**: When wrapping, preserve bullet point alignment, list indentation,
  and other structural formatting
- **Exceptions**: URLs and markdown tables are exempt from this rule

#### Hard Line Breaks (MD009 Override)

- **No trailing spaces**: Never use trailing spaces for hard line breaks
- **Always use `<br/>`**: Use HTML break tags for explicit line breaks
- **Rationale**: Trailing spaces are invisible and cause formatting issues

#### Duplicate Headings (MD024 Override)

- **Allow duplicate headings**: Headings in the same document may have identical text
- **Rationale**: Document structure may require repeated section names

#### Reference Links (Custom Requirement)

- **Prioritize reference links**: Use `[text][ref]` format over inline links
- **Inline link limit**: Avoid inline links when the URL is long or complex
- **Reference placement**:
  - Single use: Place reference at bottom of current heading section
  - Multiple use: Place reference at bottom of entire document
- **Reference naming**: Use meaningful, descriptive reference names

Example of preferred reference link format:

```markdown
## Installation

Follow the [installation guide][install-guide] to get started.

### Advanced Setup

For complex configurations, see the [advanced guide][install-guide].

[install-guide]: https://example.com/very/long/installation/guide/url
```

#### Line Wrapping Best Practices

When wrapping long lines, maintain proper formatting:

**Lists:**

```markdown
- This is a very long list item that exceeds the 100-character limit and
  needs to be wrapped with proper indentation
  - Nested items should maintain their indentation level when wrapped across
    multiple lines
```

**Paragraphs:**

```markdown
This is a long paragraph that needs to be wrapped. The continuation should
start at the beginning of the line without additional indentation unless
required by the context.
```

**Code blocks and URLs remain unchanged:**

```bash
very-long-command --with-many-parameters --that-exceed-the-line-limit --but-should-not-be-wrapped
```

Visit [this very long
URL](https://example.com/very/long/url/that/exceeds/character/limits/but/should/not/be/wrapped)

### Enforcement Policy

- **All markdown files** created or modified must pass markdownlint validation with the above custom
  overrides
- **Comprehensive compliance** with the entire markdownlint ruleset
- **No exceptions** beyond those explicitly listed in the custom overrides
- **Consistent application** across all markdown content

#### Markdown Creation Protocol

**MANDATORY**: Before completing any markdown content creation or modification, Claude must
preemptively ensure compliance with all markdownlint rules and custom overrides.

**Universal Application**: Apply these rules to ALL markdown content, including:

- Any file containing markdown (regardless of extension)
- Markdown-formatted responses and replies from Claude
- Documentation within code files
- Any other markdown content in any context

**Pre-Completion Requirements**:

- Line length ≤ 100 characters with proper hard-wrapping
- Reference links used for complex URLs instead of inline links
- No trailing spaces for line breaks (use `<br/>` instead)
- Blank line after every heading before content
- Language specification for all fenced code blocks
- Full markdownlint rule compliance
- Custom overrides properly applied

**Awareness Expectation**: Claude must be inherently aware of markdown formatting requirements
and write compliant content from the start, rather than requiring post-creation validation
tooling.
