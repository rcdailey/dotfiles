# Claude Code Instructions

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

- **Maximum line length**: 100 characters (not 80)
- **Hard requirement**: No line of text may exceed 100 characters
- **Line breaks**: Use hard line breaks to wrap long lines
- **Formatting**: Maintain proper indentation and formatting when wrapping
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

Visit [this very long URL](https://example.com/very/long/url/that/exceeds/character/limits/but/should/not/be/wrapped)

### Enforcement Policy

- **All markdown files** created or modified must pass markdownlint validation
  with the above custom overrides
- **Comprehensive compliance** with the entire markdownlint ruleset
- **No exceptions** beyond those explicitly listed in the custom overrides
- **Consistent application** across all markdown content
