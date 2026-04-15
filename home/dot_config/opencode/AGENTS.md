# Global Directives

## Core Rules

- Limit conversational responses to 4 lines unless user requests detail or asks "why"/"how". Omit
  preambles, postambles, and wrapper phrases. Answer only what's asked with one-word/sentence
  answers when sufficient. This applies to conversation only, not work artifacts.
- MUST NOT use emojis, em dashes (\u2014), en dashes (\u2013), curly quotes
  (\u201C\u201D\u2018\u2019), or Unicode symbols in any output. Use commas, semicolons, or
  parentheses instead of dashes for parenthetical content. Use straight quotes. Preserve existing
  symbols when editing others' content.
- Vary punctuation naturally. Avoid defaulting to hyphens/dashes for joining clauses or
  parenthetical content. Use periods for independent thoughts, semicolons for closely related
  clauses, parentheses for de-emphasized asides, and dashes only for emphatic interruptions.
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
- Prefer structured output (JSON + jq) over table/text for CLI tools that support it (aws, gh,
  kubectl, docker). Structured output is parseable, filterable, and scriptable.

## Architecture

Apply KISS, DRY, SOLID, YAGNI. Pragmatism over dogma.

- Every abstraction must justify its existence with concrete current needs.
- Collapse indirection layers that just delegate without adding value.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n×m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Testing

Test at the highest scope that's practical. Write a failing test for the happy path first, implement
until it passes, then check coverage for gaps. Push to lower-scoped tests only when higher-scoped
tests cannot reach specific code paths.

**Test behavior, not implementation.** Skip anything with no meaningful behavior to verify:

- Output formatting (console output, log messages, UI rendering)
- Data containers with no logic (no conditionals, no transformation)
- Implementation details that could change without affecting outcomes

**Assert outcomes, not interactions.** Verify the result, side effect, or state change rather than
asserting a mock method was called. Interaction verification couples tests to implementation; they
break on refactors even when behavior is correct. If interaction verification feels like the only
option, challenge the design first (void method hiding a meaningful result, missing return value,
side effect with no observable state change).

**Debugging test failures:** Gather evidence before changing code. Avoid guess-and-check cycles.

1. Read assertion output carefully; diff output often reveals the issue immediately
2. Add adhoc logs to trace execution; remove when done
3. Compare with passing tests to spot differences
4. Add intermediate assertions to pinpoint divergence
5. Simplify to minimal reproduction; strip test down, add back until failure
6. Write adhoc granular tests to isolate suspected areas; remove when done
7. Check test isolation: run alone (`--filter` or equivalent) vs. suite to detect state leakage

**Test framing:** Tests serve as documentation. Positive tests verify expected behavior, then check
absence of side effects. Negative tests assert the error/rejection IS raised. Both are equally
important.

**Anti-patterns:**

- Over-mocking or mocking business logic
- Tests coupled to implementation details
- Duplicate coverage for same logical paths
- Production code added solely for testing
- Unexplained magic constants

## Tools

- Bash text/file search: `rg "pattern"` (text), `rg --files -g "pattern"` (files),
  `--glob "!**/exclude/**"` (filter). Unescaped `|` for alternation (`rg "foo|bar|baz"`).
- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use `gh-review` for PR review operations (pending reviews, inline comments). MUST use instead of
  raw `gh api` for review mutations. Commands: `view`, `start`, `delete`, `comment`.
- Use Context7 MCP (`resolve-library-id` then `query-docs`) for library and framework documentation
  lookups. Context7 returns current, version-specific docs and code examples directly; prefer it
  over delegating to the researcher subagent for API usage, configuration, migration guides, and
  "how do I do X with library Y" questions. Fall back to the researcher only when Context7 lacks
  coverage or the question spans multiple projects, community discussions, or issue trackers.
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for PDF files: `pdf2md <file-or-url>`. Run `pdf2md --help` for full usage.
- MUST NOT use the 'write' tool if a file exists. MUST use 'edit' tools for surgical edits to
  existing files. It is critical to respect this rule for token efficiency.

## Skills

You MUST check the available skills list before performing any task. If a skill's trigger condition
matches the current task, load it BEFORE acting on the governed task. Failure to load a matching
skill violates this directive. Skills MUST be loaded alone (never in parallel with other tool calls)
and MUST complete before acting on the governed task; loading a skill in parallel with the action it
governs means the instructions arrive too late.

## Agents

- When delegating to subagents, explicitly require them to respond directly to the caller; MUST NOT
  write research, outcomes, or responses to files on disk.
- Callers MUST cross-reference subagent findings before acting on them. This doesn't mean repeating
  the work; it means spot-checking reported results against primary sources (reading cited files,
  verifying links, searching docs, etc.) to catch hallucinations and false assumptions. Subagent
  models are weaker than the caller; trust but verify.
- For deep exploration of external GitHub repos, see the build agent's instructions. Subagents
  (researcher, etc.) MUST use their designated tools (`research scout`, `research gh`) for repo
  exploration; they MUST NOT clone repos or use local file tools.
