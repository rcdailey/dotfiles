---
name: gh-pr-review
description: Use when reviewing pull requests on GitHub
---

# PR Review

## Critical Rules

- NEVER submit reviews. The user manually submits pending reviews via GitHub UI.
- All comments MUST go through a pending review. Never post comments directly.
- When any comment targets a line outside diff hunks (non-zero exit from `review-comment`), do NOT
  retry or relocate it. Collect all failures and report them to the user so they can post those
  comments manually through the GitHub UI.

## Pending Review Workflow

### Check for existing pending review

```sh
gh-scout pr review-view owner/repo 42
```

If a pending review exists, reuse its `PRR_...` ID.

### Start a pending review

Only if no pending review exists.

```sh
gh-scout pr review-start owner/repo 42
```

Output:

```txt
id: PRR_kwDOAAABbcdEFG12
state: PENDING
```

### Add comment (single line)

```sh
gh-scout pr review-comment owner/repo 42 \
  --review-id PRR_kwDOAAABbcdEFG12 \
  --path internal/service.go \
  --line 42 \
  --body "nit: prefer helper"
```

### Add comment (multi-line)

The `--line` is the end line; `--start-line` is the beginning.

```sh
gh-scout pr review-comment owner/repo 42 \
  --review-id PRR_kwDOAAABbcdEFG12 \
  --path internal/service.go \
  --start-line 10 \
  --line 15 \
  --body "Extract this block into a helper"
```

Optional flags: `--side LEFT|RIGHT` (default RIGHT), `--start-side LEFT|RIGHT`.

### Delete a pending review

```sh
gh-scout pr review-delete PRR_kwDOAAABbcdEFG12
```

## Line Targeting Constraints

GitHub's API only supports comments on lines within diff hunks (changed lines plus a few lines of
surrounding context). Lines in the gap between hunks cannot be targeted.

When `review-comment` targets a non-diff line, it exits non-zero with:

```txt
error: path/file.cs L21 is outside the diff hunks. GitHub API does not support
comments on non-diff lines. Post this comment manually through the GitHub UI.
```

**When this happens:**

1. Continue posting remaining comments that target valid lines.
2. After all comments are posted, report the failures to the user with file, line, and the intended
   comment body so they can post manually.

**When writing suggestion blocks:** The `--start-line` to `--line` range defines what GitHub
replaces when a suggestion is applied. The range MUST exactly match the lines being replaced. Do NOT
include surrounding context lines in the range; they will be deleted.

## ID Formats

- `PRR_...`: Review node ID (from `review-start` or `review-view`)
- `PRRT_...`: Thread node ID (from `review-comment` or `review-view`)

## Output

- Plain text, not JSON
- Errors go to stderr with non-zero exit
