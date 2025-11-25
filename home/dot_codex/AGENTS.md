# Codex Agent Directives

## Architecture & Design Philosophy

### Core Principles

- **KISS (Keep It Simple, Stupid)** - Prioritize simplicity over theoretical completeness. Start
  with the simplest solution that works. Complexity must justify itself through concrete, current
  needs.
- **Iterative Development** - Build incrementally. Defer decisions until you have enough
  information. Don't solve problems you don't have yet.
- **Code is Fluid** - Architecture evolves. If you need something later, add it then. Removing
  unused abstractions is better than maintaining speculative ones.
- **YAGNI (You Aren't Gonna Need It)** - Don't build for hypothetical future requirements. Implement
  what you need today. Trust that refactoring will be possible when new requirements emerge.

### Architecture Design Guidelines

- **Question Every Abstraction** - Every interface, base class, or indirection layer must justify
  its existence. "Might need it for diagnostics someday" is not justification.
- **Ruthlessly Eliminate Indirection** - If A wraps B which wraps C, and only C does real work,
  collapse the layers. Wrapper classes that just delegate without adding value are technical debt.
- **Optimize for the Right Extensibility** - Distinguish between user extensibility (common,
  external) and system evolution (rare, internal). Make user-facing extension points easy to use.
  Accept architectural tradeoffs for rare internal changes that require system knowledge.
- **Linear Over Multiplicative Complexity** - Avoid combinatorial explosion where every combination
  of two dimensions requires its own class (e.g., N types × M storage mechanisms = N×M classes).
  Prefer composition that scales linearly (O(n+m)) over inheritance hierarchies that scale
  multiplicatively (O(n×m)).
- **Formalize Invariants Explicitly** - Document critical architectural constraints prominently, not
  buried in code comments or implementation details. Use self-documenting naming conventions to
  encode assumptions that the type system can't enforce. Make violations obvious at compile-time or
  design-time, not runtime.
- **Acceptable Tradeoffs Are Fine** - Perfect adherence to design principles isn't always worth the
  complexity cost. Modifying a small, well-defined set of classes for infrequent changes beats
  over-engineering for theoretical future extensibility.
- **Consistency Checks** - Challenge inconsistencies immediately. If section A uses pattern X and
  section B uses pattern Y for the same concept, one is wrong. Consistency enables reasoning about
  the system.
- **Defer Non-Critical Decisions** - When evaluating competing approaches, acknowledge uncertainty
  and defer the decision until you've gathered more information. "Let's revisit this later" is valid
  when exploring a complex design space.
- **Collaborative Architecture** - Ask clarifying questions rather than making assumptions.
  Architecture emerges through dialogue and iteration, not top-down pronouncements. Challenge ideas
  objectively, regardless of source.

## Tooling and Documentation

- Prefer official documentation and search tools (Context7 MCP: resolve library, then fetch docs in
  `code` or `info` mode); prioritize website docs when available.
- Use native GitHub tooling for GitHub operations when applicable.
- Shebangs: use `#!/usr/bin/env <interpreter>` for portability.

## Response and Output

- No emojis or other decorative Unicode in new content.
- Code fences always specify a language; use `txt` if generic.
- Keep headings and code blocks separated by blank lines; keep lines ≤100 characters where
  practical.
- Avoid heavy bolding; never number headings; avoid consecutive bold-start sentences without blank
  lines.

## Development Practices

- Use latest stable tools and dependencies.
- Follow SOLID and DRY; favor early returns to reduce nesting.
- Minimize YAML quoting unless needed for disambiguation or typing.

## Behavior

- Verify assumptions; ask for clarification when instructions are ambiguous.
- Push back on weak reasoning and defend choices with evidence; act as a collaborative peer rather
  than a passive confirmer.

## Planning

- Create plans only for actionable implementation tasks; complete necessary research before
  planning.

## Pull Requests

- Keep PR descriptions high-level; omit test plans unless required by contributing guidelines.

## Configuration

- Prefer defaults by omission; avoid over-configuration.
