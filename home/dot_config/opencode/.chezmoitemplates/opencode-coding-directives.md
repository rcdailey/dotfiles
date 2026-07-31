## General

- Fenced code blocks require a language specifier (use `txt` if none applies).
- Keep lines <= 100 chars. Blank lines around headings and code blocks.

## Development

- Use latest stable versions of tools, languages, libraries, frameworks.
- Prefer idiomatic patterns: use framework-native solutions over hand-rolled equivalents, current
  API surfaces over deprecated predecessors, and official usage recommendations over ad-hoc
  approaches.
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
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for PDF files: `pdf2md <file-or-url>`. Run `pdf2md --help` for full usage.
- The Glob tool skips dot-directories (`.github/`, `.vscode/`, etc.). For those, use bash:
  `rg --files --hidden -g "pattern" --glob '!**/.git/**'`.

{{ template "opencode-research-cli.md" . }}
