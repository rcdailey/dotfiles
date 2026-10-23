# Global Directives

## Core Rules

- Resolve minor ambiguity using available context and tools. Ask before proceeding when missing
  information could materially change the outcome; do not guess.
- Deliver what was asked, at the scope intended. MUST NOT expand into adjacent work, add unrequested
  features, or reframe the task.
- MUST NOT substitute a different approach when the requested one turns out to be hard, blocked, or
  unworkable. Full stop, report what blocked you and the options you see, and wait for direction. A
  change of direction requires explicit approval.
- Match user-facing written artifact length to substance. MUST NOT pad with filler sections,
  redundant summaries, or boilerplate. This rule does not govern prompts sent to subagents.
- Don't provide time estimates.
- Stop every background process and container you started once its purpose is done (including after
  smoke tests pass); leave ones that were running before you started.

## System Reminders

`<system-reminder>` blocks are system-injected, not written by the user.

## Output

Reference code with `file_path:line_number` pattern for source navigation.

## CLI Prose Arguments

Prose bound for a CLI (PR bodies, review comments, issue text, release notes) MUST be inlined via
quoted heredoc; MUST NOT be staged in a temp file and passed with `--body-file`/`-F`. The quoted
delimiter blocks expansion of `$` and backticks. Bodies rendered as markdown MUST NOT be hard
wrapped; one line per paragraph.

```sh
gh pr create --title "..." --body "$(cat <<'EOF'
Paragraph text, unwrapped.
EOF
)"
```

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

## Architecture

Apply KISS, DRY, SOLID, and YAGNI pragmatically.

- Refactor affected code when that removes duplication, special cases, or accumulated indirection.
- Collapse indirection layers that delegate without adding value.
- Prefer removing obsolete code and straightforward solutions over parallel paths or cleverness.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n\*m)).
- Document architectural constraints prominently; make violations obvious at design-time.

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
- Prefer structured output (JSON + jq/yq) for CLIs that support it (aws, gh, kubectl, docker), but
  print only projected fields: filter at the source, project with jq/yq (`@tsv` for rows), cap
  output near 50 lines and 200 columns, and search unstructured text with `rg`. Widen only when the
  narrowed result is insufficient.

## Code Documentation

- Document a type or member, regardless of visibility, when its purpose, responsibility boundaries,
  guarantees, or lifecycle constraints cannot be easily inferred from its code and name. Write for
  maintainers who do not know the subsystem; explain unfamiliar domain terms; do not paraphrase
  names. Use natural prose rather than a required template.
- Do not require boilerplate for parameters, return values, exceptions, or similar structural
  details. Document them only when they carry consequential meaning.
- Keep shared documentation on the contract that declares the behavior rather than duplicating it
  across implementations.
- Verify documented guarantees against implementation and callers. Update documentation when the
  contract changes; do not document intended behavior as an existing guarantee.
- Apply these rules to new and changed contracts. Do not backfill unrelated code.

## Testing

Load the `testing` skill before writing, changing, or diagnosing tests.

## Git

- When creating local branches, MUST NOT set a tracking branch initially (`git checkout -b` or
  `git branch` without `-t`/`--track`). Tracking is set later via `git push -u`.
- The user creates worktrees; never create one.

## Repository Locations

- Personal projects live in `~/code/<repo>`; forks of third-party repositories the user contributes
  to live in `~/code/forks/<repo>`. Reuse an existing clone before creating one.
- To fork and clone, run `gh repo fork <owner>/<repo> --clone` from `~/code/forks/`. It reuses an
  existing fork and sets `origin` to the fork and `upstream` to the parent. Do not add `--remote`;
  it applies only inside an existing clone.
- Read third-party repositories without planned contributions through `gh`, or clone them under
  `/tmp/pi/`.
- Put repository-specific mise tools and env, including secrets, in that repository's
  `mise.local.toml`. The global gitignore excludes `*.local.toml`; never add these values to a
  tracked mise config.

## Tools

- Shebangs: `#!/usr/bin/env bash` for shell scripts; `#!/usr/bin/env -S uv run --script` for Python
  scripts, declaring third-party dependencies in an inline `# /// script` metadata block so uv
  installs them on first run.
- Use fff search tools for text and path discovery and pi-lens tools for symbol navigation and
  diagnostics.
- Use `gh` CLI for GitHub operations (issues, PRs, releases, repos, auth, mutations).
- Use `pdf2md` for local PDF files: `pdf2md <file>`. Run `pdf2md --help` for full usage.
- Keep stderr visible (`2>&1`, not `2>/dev/null`) when parsing or reporting command output; a hidden
  usage error reads as empty data. Run `<cli> --help` before guessing a subcommand.

## Shell Search

MUST use `rg` (ripgrep) over `grep`. MUST use `rg --files -g` over `find -name`. Both are enforced
by best-effort guards for ordinary shell invocations, not a security boundary. Nested scripts,
aliases, and unsupported shell syntax still require agent compliance.

ripgrep is recursive by default; no flag enables it. `-r` is `--replace=REPLACEMENT`: it takes an
argument, so `rg -r "pattern" path/` consumes `pattern` as replacement text and searches for `path/`
instead. MUST NOT use `-r` or `-rl` for recursion. Common patterns:

```sh
rg "pattern" path/              # recursive content search (default)
rg -n "pattern" path/           # with line numbers
rg -l "pattern" path/           # files containing matches
rg -c "pattern" path/           # match count per file
rg -i / -w / -F "pattern"       # case-insensitive / whole-word / literal
rg -A3 -B3 "pattern"            # context lines after/before
rg --files -g "*.yaml" path/    # find files by glob (replaces find -name)
rg -g "*.py" "pattern" path/    # restrict search to a glob
rg --hidden -g "!**/.git/**"    # include dot-directories
```

## GitHub API

- `gh api` commands MUST use `--method` explicitly.

## Citations

- Citations MUST be literal URLs fetched in the current session. No bracket indices, no placeholder
  references, no carry-forward from prior turns or prior searches. If a URL was not fetched this
  session, the citation does not exist and MUST be omitted. Search results and snippets are
  discovery only; they do not make linked URLs citable. A missing citation beats an unverified one.
