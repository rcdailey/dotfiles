---
name: exploring-github
description: >-
  Use when exploring remote GitHub repositories, browsing repo contents,
  reading remote files, searching code, inspecting
  issues/PRs/discussions/commits/releases, comparing refs or tags, or viewing
  blame
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
gh-scout orient      REPO [--brief]                    # metadata, tree, key files
gh-scout ls          REPO [PATH] [--limit N]           # list directory
gh-scout read        REPO PATH [--limit N] [--offset N] # read file contents
gh-scout tree        REPO [--limit N]                   # recursive file listing
gh-scout commits     REPO [--author X] [--path P]       # commit history
gh-scout blame       REPO PATH                          # line-by-line attribution
gh-scout compare     REPO BASE HEAD                     # diff between two refs
gh-scout issues      REPO [NUMBER] [--state S] [--search Q]  # list or detail
gh-scout discussions REPO [NUMBER] [--category C]            # list or detail
gh-scout prs         REPO [NUMBER] [--state S] [--search Q]  # list or detail
gh-scout releases    REPO [TAG]                              # list or detail
```

Search commands do not take a positional REPO; scope with flags instead:

```txt
gh-scout repo-search QUERY [--sort stars] [--stars ">=N"] [--language L] [--topic T]
gh-scout code-search QUERY [--repo OWNER/REPO]  # --repo is repeatable
```

Most commands also accept `--ref REF` (branch/tag/SHA) and `--limit N`.

`orient` always shows the README (up to 200 lines, with a truncation notice). `--brief` skips the
remaining key file contents (metadata + structure + languages + contributors + README only). Use it
when surveying multiple repos to reduce output volume, then `read` specific files as needed.

## Exploration Strategy

Follow broad-then-narrow:

1. **Discover** -- when searching for repos by topic or popularity, start with `repo-search`. Use
   `code-search` only when looking for specific code patterns across repos.
2. **Orient** -- `gh-scout orient owner/repo` fetches metadata, structure, languages, top
   contributors, and key project files in one call. Use `--brief` when surveying multiple repos.
3. **Survey** -- use `ls` and `read` to examine specific directories and files identified during
   orient.
4. **Target** -- use `code-search` to find specific patterns, `commits` to trace history, `blame` to
   attribute changes.
5. **Cross-reference** -- trace from code to PRs/issues with `prs`, `issues`. Compare releases with
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

## Tips

- `read` on a directory path auto-detects and prints a listing (like `ls`). No need to check whether
  a path is a file or directory first.
- For large files, use `--offset` to paginate. Read lines 0-499 first (`--limit 500`), then continue
  with `--offset 500 --limit 500`. Avoid piping through `head`; use `--limit` instead.
- `code-search` uses the GitHub code search API, which does NOT support regex. Queries like
  `"foo\|bar"` or `"foo.*bar"` will not work as expected. Run separate searches for each term or use
  GitHub qualifier syntax (`foo OR bar`).
- `code-search` qualifiers (`language:`, `path:`, `org:`, etc.) go INSIDE the query string, not as
  separate CLI args. Example: `gh-scout code-search "changelog language:go"` (correct) vs `gh-scout
  code-search "changelog" language:go` (argparse error).
- Use `repo-search` (not `code-search`) when looking for repositories by topic, popularity, or
  language. `code-search` returns file matches; `repo-search` returns repos with stars and metadata.
- Issue and discussion detail views show emoji reaction breakdowns (upvotes, hearts, etc.).
  Discussion detail also shows the accepted answer when present.
- `discussions` supports `--category`, `--answered`, and `--unanswered` filters. Categories are
  matched case-insensitively by name.
- Do not pipe gh-scout output through `grep` or `head`. Use built-in flags (`--limit`, `--offset`,
  `--search`, `--state`) to filter results at the source.

## Error Handling

- Rate limited: reduce `--limit` or wait and retry
- 404 on a path: verify the ref and path exist; the repo may have been renamed or the branch deleted
- Truncated tree: use `gh-scout ls` to navigate directories incrementally instead of full tree
