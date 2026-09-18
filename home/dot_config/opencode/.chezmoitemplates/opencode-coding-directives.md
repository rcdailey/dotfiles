## Implementation Discipline

Before editing, trace the affected flow and inspect relevant callers.

- Build only for current requirements. Add abstractions, configuration, extensibility, or
  scaffolding only when a current variation or boundary requires them.
- Prefer, in order: existing coherent code, standard-library or native platform/framework behavior,
  an installed dependency, then the smallest new implementation.
- Add a dependency only when it reduces lifecycle complexity enough to justify its operational and
  security cost.
- Optimize for lifecycle simplicity, not line or file count. Do not trade away required
  architecture, tests, operability, trust-boundary validation, data-loss prevention, security, or
  accessibility.
- Reuse code only when semantics and change cadence align; do not couple unrelated behavior merely
  to remove similar lines.
- Fix defects at the narrowest shared invariant and keep unrelated cleanup separate.
- Between equally simple options, choose the one correct at the relevant boundaries.
- When a deliberate simplification has a known ceiling, document the ceiling and the trigger for
  replacing it.

## General

- Fenced code blocks require a language specifier (use `txt` if none applies).
- Keep code and authored file content <= 100 chars per line; this limit does not apply to chat.
- Use blank lines around headings and code blocks.

## Development

- Use current stable versions for new selections. Preserve repository version constraints unless an
  upgrade is requested.
- Prefer current, idiomatic APIs and official usage recommendations over deprecated or ad-hoc
  approaches.
- Reduce nesting: invert conditions, exit early.
- YAML: don't quote values unless required for disambiguation.
- Prefer defaults by omission over explicit configuration.
- Comments must earn their place by reducing cognitive load. Prefer self-documenting naming.
- When affected code uses inconsistent patterns, unify them rather than adding a third approach.
- MUST NOT use the 'write' tool on an existing file; use 'edit' tools for surgical edits. Full-file
  rewrites waste tokens and risk clobbering unseen content.
- For current library or framework APIs, MUST use `ctx7` first. Run `ctx7 library <name> <query>` to
  resolve a library ID, then `ctx7 docs <library-id> <query>` for the relevant API. Use official
  sources when Context7 lacks coverage.
- Keep PR descriptions high-level, focused on the change. Skip test plans and template boilerplate.
- Prefer structured output (JSON + jq) over table/text for CLI tools that support it (aws, gh,
  kubectl, docker). Structured output is parseable, filterable, and scriptable.

## Public Contract Documentation

- Document hand-written public types and exported contracts for maintainers who do not know the
  subsystem. Explain purpose and unfamiliar domain terms; do not paraphrase names.
- Document members selectively when their signatures and enclosing documentation leave important
  contract meaning unexplained, or meaning cannot be easily inferred from code alone.
- Explain responsibility boundaries, consumer-visible guarantees, and lifecycle constraints when
  relevant. Use natural prose rather than a required template.
- Do not require boilerplate for parameters, return values, exceptions, or similar structural
  details. Document them only when they carry consequential contract meaning.
- Do not document non-public implementation details by default.
- Keep shared documentation on the contract that declares the behavior rather than duplicating it
  across implementations.
- Verify documented guarantees against implementation and callers. Update documentation when the
  contract changes; do not document intended behavior as an existing guarantee.
- Apply these rules to new and changed contracts. Do not backfill unrelated code.

## Git

- When creating local branches, MUST NOT set a tracking branch initially (`git checkout -b` or `git
  branch` without `-t`/`--track`). Tracking is set later via `git push -u`.
- For UD/DU conflicts (file deleted on one side, modified on the other), MUST NOT blindly accept the
  deletion. Run `git diff REBASE_HEAD...HEAD -- <file>` to see the upstream modifications being
  discarded, then port any meaningful changes to the replacement files before resolving with `git
rm`.

## Architecture

Apply KISS, DRY, SOLID, and YAGNI pragmatically.

- Refactor affected code when that removes duplication, special cases, or accumulated indirection.
- Collapse indirection layers that delegate without adding value.
- Prefer removing obsolete code and straightforward solutions over parallel paths or cleverness.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n\*m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Tools

- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use glob, grep, and targeted reads for symbol and text discovery. Use project lint, typecheck, and
  compiler commands for diagnostics until OpenCode V2 restores its LSP runtime.
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for local PDF files: `pdf2md <file>`. Run `pdf2md --help` for full usage.
- The Glob tool skips dot-directories (`.github/`, `.vscode/`, etc.). For those, use shell: `rg
--files --hidden -g "pattern" --glob '!**/.git/**'`.
