---
name: exploring-github
description: >-
  Use when exploring remote GitHub repositories, browsing repo contents,
  reading remote files, searching code, inspecting issues/PRs/commits/releases,
  comparing refs or tags, or viewing blame
---

# Exploring GitHub

Use `gh-scout` for all remote GitHub repository exploration. It wraps `gh` CLI with token-optimized
plain text output, sensible defaults, and simplified syntax. Run `gh-scout --help` for the full
command reference.

## Prerequisites

Requires `gh` (authenticated) on PATH. If missing, the script fails early with a clear message.

## Subcommands

All output is plain text (no JSON). List/detail commands are consolidated: pass an identifier (issue
number, PR number, release tag) to get detail; omit it to list.

- `orient` -- metadata, languages, contributors, file tree, key files (README, etc.)
- `ls`, `read`, `tree` -- browse and read files
- `code-search` -- search code across GitHub or scoped to a repo
- `commits`, `blame`, `compare` -- history and attribution
- `issues` -- list or detail (`issues REPO` vs `issues REPO 42`)
- `prs` -- list or detail (`prs REPO` vs `prs REPO 42`)
- `releases` -- list or detail (`releases REPO` vs `releases REPO v1.0`)

## Exploration Strategy

Follow broad-then-narrow:

1. **Orient** -- `gh-scout orient owner/repo` fetches metadata, structure, languages, top
   contributors, and key project files in one call. Always start here.
2. **Survey** -- use `ls` and `read` to examine specific directories and files identified during
   orient.
3. **Target** -- use `code-search` to find specific patterns, `commits` to trace history, `blame` to
   attribute changes.
4. **Cross-reference** -- trace from code to PRs/issues with `prs`, `issues`. Compare releases with
   `compare`.

Run independent gh-scout calls in parallel. For example, read multiple files simultaneously or
search while listing a directory.

## Subagent Delegation

GitHub exploration generates noisy intermediate output (trees, file contents, API responses).
Delegate to a subagent (Task tool) and return only the synthesized answer. This keeps the main
conversation clean and avoids context bloat.

## Stop Conditions

Pause and ask the user when:

- The repository is private and access is denied (404)
- The question is ambiguous enough that multiple exploration paths seem equally valid
- The tree is very large (truncated) and you are unsure which area to focus on
- You have read 15+ files without finding what you need

## Error Handling

- Rate limited: reduce `--limit` or wait and retry
- 404 on a path: verify the ref and path exist; the repo may have been renamed or the branch deleted
- Truncated tree: use `gh-scout ls` to navigate directories incrementally instead of full tree
