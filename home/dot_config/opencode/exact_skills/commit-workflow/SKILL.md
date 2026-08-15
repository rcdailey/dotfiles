---
name: commit-workflow
description: >-
  Use when staging changes, creating commits, splitting work into commits, or selecting partial
  file hunks non-interactively. Covers direct Git inspection, commit message composition, the
  `commit save` workflow, and `git hunks`. Do not use for pushing or unrelated Git operations.
---

# Commit workflow

Use session context as the authority for why the change exists and repository state as the authority
for what changed. Create commits directly; do not delegate them.

## Inspect and group

- Inspect only what remains uncertain. Start with `git status --short`; use stats, targeted diffs,
  or history only when they answer a specific scope or behavior question.
- A full diff is unnecessary when you authored and verified the exact unchanged content in this
  session. Inspect any pre-existing, independently edited, or ambiguous changes before committing.
- Keep independently reviewable concerns in separate commits. Respect a user-specified scope or
  commit count.
- Use `commit save`, never raw `git commit`. Run `commit save --help` for ordinary flag syntax.

## Compose the message

Follow repository-owned commit rules. Otherwise use `type(scope): description` with one of: `feat`,
`fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`, or `revert`.

- Choose the type by intent: behavior uses `feat` or `fix`; structure-only changes use `refactor`;
  documentation uses `docs`; tests use `test`; tooling, configuration, and dependencies use `chore`;
  pipelines use `ci`; performance work uses `perf`.
- Use imperative mood, no trailing period, and describe the outcome rather than the editing action.
- Treat session context as authoritative for motivation and the diff as authoritative for
  implementation. Do not infer implementation claims from intent alone.
- Before drafting, inventory:
  - motivation or root cause
  - durable contract, data-flow, and architectural changes
  - constraints and behavior deliberately preserved
  - temporary migration scaffolding and its removal condition
  - deferred work and the issue or boundary that owns it
  - the compatibility boundary: released behavior, user data, wire API, or branch-local transition
- Treat an item as material when it changes a contract, boundary, invariant, or future decision.
  Tests, file counts, and implementation mechanics are not material unless they explain safety.
- Cover every material inventory item in the subject, a `-p` paragraph, or a `-c` entry. Related
  items may share a paragraph; an issue reference never substitutes for commit-local rationale.
- For a cross-boundary or migration commit, the body MUST distinguish the durable design from the
  temporary bridge and state what remains intentionally unchanged or deferred.
- Preview with `commit save -n`, then compare the rendered message against the inventory. Revise
  before saving if a reviewer could not recover the design constraints and migration boundary.
- Add one changelog entry per material outcome when a commit has multiple distinct outcomes. Do not
  repeat those details in the paragraph.
- Pass issue references supplied by the user with `-i`; never invent them.

## Stage and save

Choose one mode:

- Existing index: verify `git diff --cached`, then run `commit save` without file arguments.
- Whole files: pass the paths to `commit save`; it resets the index and stages only those files.
- Entire worktree: pass `-a` to `commit save`.
- Partial files: use the workflow below.

For partial staging:

1. Inspect the existing index; preserve user-staged content unless the user requests otherwise.
2. Run `git hunks list`, then stage quoted IDs with `git hunks add '<id>'...`.
3. For an untracked file, run `git add -N -- <path>` before listing its hunks.
4. Stage any complete files with `git add -- <paths>`.
5. Verify the complete staged result with `git diff --cached`.
6. Run `commit save` without file arguments. Passing paths would reset the partial selection.

Hunk IDs remain stable while other hunks are staged, but not after editing the worktree. A failed
multi-hunk add may leave earlier requested hunks staged; always verify the index before saving.

If hooks reject file content, fix the reported issue and rerun the relevant checks before saving
again. Do not bypass repository hooks. After success, report the short SHA and subject.
