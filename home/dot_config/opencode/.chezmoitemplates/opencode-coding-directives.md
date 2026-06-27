## Chat Style

Governs session chat only, NEVER work artifacts (code, docs, PR bodies, commits).

- Drop filler words: just, really, basically, actually, certainly, of course, essentially,
  importantly, it's worth noting, as mentioned.
- Lead with the answer or action. Stop when complete.
- Fragments OK. Short synonyms over long ones. One sentence beats two when meaning is preserved.
- When explaining, use causal chains (A causes B, B causes C). Name technical concepts inline
  parenthetically so the user can ask for depth selectively.

**Anti-patterns:**

- Not: "I'll check the config file to see if the setting exists." Yes: (reads file, states finding)
- Not: "The issue is that your configuration has an incorrect value for the timeout setting, which
  is causing the connection to fail before the server can respond." Yes: "Timeout too low in config.
  Server can't respond in time."
- Not: "Sure! Let me help you with that. I'll start by looking at..." Yes: (starts doing it)
- Not: "Based on my analysis of the codebase, I've identified several potential issues..." Yes:
  "Three issues:" (lists them)

## General

- Fenced code blocks require a language specifier (use `txt` if none applies).
- Keep lines <= 100 chars. Blank lines around headings and code blocks.

## Development

- Use latest stable versions of tools, languages, libraries, frameworks.
- Prefer idiomatic patterns: use framework-native solutions over hand-rolled equivalents, current
  API surfaces over deprecated predecessors, and official usage recommendations over ad-hoc
  approaches. SHOULD verify against `ctx7` when writing non-trivial integrations with libraries,
  frameworks, tools, or language features; model training data may reflect outdated or incorrect
  idioms.
- Reduce nesting: invert conditions, exit early.
- YAML: don't quote values unless required for disambiguation.
- Prefer defaults by omission over explicit configuration.
- Comments must earn their place by reducing cognitive load. Prefer self-documenting naming.
- Match existing codebase patterns rather than introducing new ones. When inconsistencies exist,
  unify them rather than adding a third approach.
- Keep PR descriptions high-level, focused on the change. Skip test plans and template boilerplate.
- Prefer structured output (JSON + jq) over table/text for CLI tools that support it (aws, gh,
  kubectl, docker). Structured output is parseable, filterable, and scriptable.

## Git

- When creating local branches, MUST NOT set a tracking branch initially (`git checkout -b` or `git
  branch` without `-t`/`--track`). Tracking is set later via `git push -u`.
- For UD/DU conflicts (file deleted on one side, modified on the other), MUST NOT blindly accept the
  deletion. Run `git diff REBASE_HEAD...HEAD -- <file>` to see the upstream modifications being
  discarded, then port any meaningful changes to the replacement files before resolving with `git
  rm`.

## Architecture

Apply KISS, DRY, SOLID, YAGNI. Pragmatism over dogma.

- Every abstraction must justify its existence with concrete current needs.
- Collapse indirection layers that just delegate without adding value.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n*m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Authoring

Applies when producing AGENTS.md, SKILL.md, agent definitions, or command files.

- MUST use minimum tokens. Every word earns its place; bullet lists over paragraphs.
- MUST NOT introduce redundancies with existing content at any scope.
- MUST generalize from the concrete task. Extract the underlying principle; strip scenario-specific
  details (file types, domain objects, tool names) that won't apply to future work.
- One minimal example beats three detailed ones.
- MUST cross-reference existing guidance instead of restating. One authoritative location per
  concept; lower scopes reference higher scopes.
- MUST self-review authored content against these rules before finalizing. If a draft violates any
  rule, tighten before writing.

## Testing

SHOULD write a failing test before implementing features and fixes (test-first). Test at the highest
scope that's practical; push to lower-scoped tests only when higher-scoped tests cannot reach
specific code paths.

**Assert outcomes, not interactions.** Verify the result, side effect, or state change rather than
asserting a mock method was called. Interaction verification couples tests to implementation; they
break on refactors even when behavior is correct. If interaction verification feels like the only
option, challenge the design first (void method hiding a meaningful result, missing return value,
side effect with no observable state change). Skip anything with no meaningful behavior to verify
(output formatting, data containers with no logic, implementation details that could change without
affecting outcomes). Avoid: over-mocking, duplicate coverage, test-only production code, magic
constants.

**Debugging test failures:** Gather evidence before changing code. Avoid guess-and-check cycles.

1. Read assertion output carefully; diff output often reveals the issue immediately
2. Add adhoc logs to trace execution; remove when done
3. Compare with passing tests to spot differences
4. Add intermediate assertions to pinpoint divergence
5. Simplify to minimal reproduction; strip test down, add back until failure
6. Write adhoc granular tests to isolate suspected areas; remove when done
7. Check test isolation: run alone (`--filter` or equivalent) vs. suite to detect state leakage

## Tools

- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use `gh-review` for all PR comment operations (reading, writing, replying), instead of raw `gh
  api` or `gh pr` for any review-related task. Commands: `view`, `start`, `delete`, `comment`,
  `reply`, `edit`, `remove`. The `view` command fetches review threads and conversation comments in
  a single query with filtering and LLM-optimized output.
- `ctx7` (also called "context7") is the CLI for the Context7 documentation service; it provides
  up-to-date library and framework docs to LLMs. Use `ctx7` for library and framework docs before
  webfetch or the researcher subagent; fall back to the researcher only when `ctx7` lacks coverage:
  - `ctx7 library <name> <query>` searches the index and returns library IDs
  - `ctx7 docs <libraryId> <query>` fetches docs for an ID (e.g. `/vercel/next.js`)
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for PDF files: `pdf2md <file-or-url>`. Run `pdf2md --help` for full usage.
- The Glob tool skips dot-directories (`.github/`, `.vscode/`, etc.). For those, use bash:
  `rg --files --hidden -g "pattern" --glob '!**/.git/**'`.
- MUST NOT use the 'write' tool if a file exists. MUST use 'edit' tools for surgical edits to
  existing files. This is for token efficiency.
