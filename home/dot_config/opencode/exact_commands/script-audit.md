---
description: Retrofit a script against real session friction
---

Audit the target script against friction observed in the current session and mercilessly fix gaps,
bugs, and awkward ergonomics so the next LLM does not hit the same walls.

Arguments: $ARGUMENTS

## Target Resolution

Resolve the target script from the argument or session context:

- Explicit path (e.g., `./scripts/foo.py`, `src/cli/`) -> target is that path
- Short name (e.g., `foo`) -> search for a matching script or CLI entry point in the repo
- No argument -> infer from session: whichever script the session exercised most heavily. If
  ambiguous, ask. If the session exercised no scripts, stop and report nothing to audit.

## Context Loading

If the target has a matching skill (check available skills list), MUST load it alone (no parallel
tool calls) before reading source or editing.

If no skill exists, read the target script source in full to understand its structure, patterns, and
design intent. This replaces the skill as the "what good looks like" reference.

## Evidence: Session Friction Only

The sole evidence source is the current session. Do NOT scan git log, do NOT rg the source for
TODOs, do NOT open a broad refactor safari. Walk backward through this session and extract concrete
moments where the script failed the LLM:

- Reached past the script to a raw CLI because the script lacked the capability or produced the
  wrong shape
- Ran two or more script invocations in sequence to answer one question
- Parsed the script's output manually to pull a field that should have been surfaced directly
- Hit a resolver that rejected a reasonable input (fuzzy name, missing entity, edge case)
- Got output so verbose the response truncated or context pressure spiked
- Got output so terse a follow-up call was required for trivial context
- Worked around a bug, edge case, or missing flag with shell glue

For each friction point, record: what the LLM needed, what the script delivered, the workaround
used, and which module/command owns the gap.

If the session yielded zero friction points, stop and say so. Do not invent gaps.

## Audit Principles

When a skill was loaded, apply its design philosophy. When no skill exists, derive principles from
the script's own structure and the universal rules below:

- **Workflow, not passthrough.** A command must correlate sources, apply heuristics, or resolve
  inputs flexibly. A reformatter around one upstream call does not belong.
- **Token-optimized output by default.** Prose over JSON, fewer lines over more, key-value and
  fixed-width tables over bordered tables, omit healthy/normal rows when showing problems. Verbose
  modes are opt-in flags (`--json`, `--all`, `-v`), never the default.
- **Flexible input resolution.** Accept names, labels, prefixes, and edge-case inputs where a
  reasonable caller would expect a match.
- **Merciless refactor.** Backward compatibility is NOT a constraint. Rename flags, remove
  subcommands, restructure modules, change output shapes. No dual-support shims, no deprecation
  warnings. If an old pattern is wrong, delete it.
- **Fold follow-ups into the primary command.** If every caller of command X needs to also run Y,
  Y's output belongs inside X.

## Process

### 1. Extract Friction

Produce an inline list of friction points from the session (title, need, gap, workaround, owning
module). Keep it compact; this is working memory, not a deliverable.

### 2. Classify Fixes

For each friction point, pick one:

- **Fix in place**: bounded change to an existing command (new flag, better resolver, richer output,
  bug fix)
- **Fold together**: merge multiple commands or auto-fetch downstream context
- **New command**: the workflow is genuinely missing and earns its place
- **Out of scope**: belongs to a different tool or is a one-off; note and drop

### 3. Apply

Implement every non-dropped fix in this session. Remove superseded code outright. Update relevant
documentation (skill docs, AGENTS.md, READMEs) in the same pass when behavior or interfaces change.

### 4. Verify

Run each changed command against the live target at least once. Use the script's own invocation
pattern plus the exact invocation that exposed the friction.

Confirm output shape, token footprint (eyeball line count), and that the original workaround is no
longer needed.

If the target script has a test suite, MUST run it and fix any failures caused by the audit changes.
Update test assertions to match new behavior; do not delete tests. Add tests for new commands or
changed resolver behavior.

### 5. Report

Concise session response:

```txt
Target: <script name>
Friction points: <N>
Fixes applied:
- <command>: <one-line summary>
- ...
Removed: <flags/commands/modules deleted>
Docs updated: <paths> (or "n/a")
Deferred: <items classified out of scope, with one-line reason>
```

Keep it under 20 lines. No diff dumps; the user reads those via git.

## Rules

- MUST load the matching skill alone before any edits (when one exists)
- MUST read the full script source before any edits (when no skill exists)
- MUST NOT commit or push
- MUST NOT preserve backward compatibility; remove old flags, commands, and output shapes outright
- MUST NOT add dual-support shims, deprecation warnings, or "legacy" branches
- MUST NOT introduce structured output (JSON, YAML) as a default; use prose/key-value/tables and
  gate structure behind an explicit flag
- MUST NOT scan git history, grep for TODOs, or expand scope beyond session-observed friction
- MUST delete obsolete documentation in the same pass as the code change
- MUST cap the audit at friction points actually surfaced this session; inventing hypothetical gaps
  defeats the purpose
- MUST NOT defer fixes by claiming they are "too large"; implement every non-dropped fix or classify
  it as out of scope with a concrete reason
