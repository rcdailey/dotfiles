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

## Cheat Sheet

All output is plain text. Most commands follow `gh-scout COMMAND REPO [args]`. List/detail commands
are consolidated: pass an identifier to get detail; omit it to list.

```txt
gh-scout orient   REPO                          # metadata, tree, key files
gh-scout ls       REPO [PATH]                   # list directory
gh-scout read     REPO PATH [--limit N]         # read file contents
gh-scout tree     REPO [--limit N]              # recursive file listing
gh-scout commits  REPO [--author X] [--path P]  # commit history
gh-scout blame    REPO PATH                     # line-by-line attribution
gh-scout compare  REPO BASE HEAD               # diff between two refs
gh-scout issues   REPO [NUMBER] [--state S]     # list or detail (open/closed/all)
gh-scout prs      REPO [NUMBER] [--state S]     # list or detail (open/closed/merged/all)
gh-scout releases REPO [TAG]                    # list or detail
```

`code-search` is the exception; repo is not positional (it searches all of GitHub by default):

```txt
gh-scout code-search QUERY [--repo OWNER/REPO]  # --repo is repeatable
```

Most commands also accept `--ref REF` (branch/tag/SHA) and `--limit N`.

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
