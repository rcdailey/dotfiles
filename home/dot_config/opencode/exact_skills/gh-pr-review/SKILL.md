---
name: gh-pr-review
description: >-
  Use when reading, posting, or managing PR review comments via the `gh-review` tool: viewing
  PR comments with filtering, leaving inline comments on specific diff lines, starting or
  deleting pending reviews, replying to review threads. Triggers on phrases like "review this
  PR", "check for comments", "leave a comment on line X", "add review feedback", "start a
  pending review", "reply to the comment", or any task involving PR comments and code review.
  Do NOT use for merging, approving via `gh pr review --approve`, or non-review PR operations.
---

# PR Review

All PR comment operations (reading, writing, replying) MUST go through `gh-review`. Do NOT use raw
`gh api` or `gh pr` for any review-related task.

## Critical Rules

- NEVER submit reviews. The user manually submits pending reviews via GitHub UI.
- All new review comments MUST go through a pending review. Never post comments directly.
- When any comment targets a line outside diff hunks (non-zero exit from `comment`), do NOT retry or
  relocate it. Collect all failures and report them to the user so they can post those comments
  manually through the GitHub UI.

## Review Etiquette

### Priorities (in order)

- **Security**: Credentials, injection, auth flaws, input validation
- **Architecture**: Resource config, error handling, data loss risks, breaking changes
- **Code quality**: Duplication, logic errors, performance, missing config

Medium/low (only when explicitly requested): Organization, docs, test coverage, style, naming

### Tone

- Bugs/defects: Direct language ("I think this is a bug...", "This will cause...")
- Style/architecture: Questions ("What do you think about...", "Would it make sense to...")
- Use contractions, be conversational, comment on code not developer
- Skip comments that just repeat what other reviewers already said
- Bot comments (infer from context: `[bot]` suffix, known CI/analysis tools, automated comment
  patterns): use neutral, factual statements. Explain what was done and why, or why something will
  not be done. Do not address the bot conversationally or phrase replies as if speaking to a person.

### Verification

Use `ctx7` and web search to verify unfamiliar patterns, best practices, and security implications
before writing comments. Every technical claim must be verified.

## Reading Comments

Use `gh-review view` to read PR comments. It fetches review threads, conversation comments, and
pending reviews in a single query with LLM-optimized prose output.

### Default (unresolved threads only)

```sh
gh-review view owner/repo 42
```

### Threads needing attention (PR author hasn't replied last)

```sh
gh-review view owner/repo 42 --unanswered
```

### No bot noise

```sh
gh-review view owner/repo 42 --no-bots
```

### Recent comments only

```sh
gh-review view owner/repo 42 --since 2d
```

Accepts relative durations: `30m`, `1h`, `2d`, `1w`.

### Show everything (including resolved)

```sh
gh-review view owner/repo 42 --all
```

### Options

- `--all`: show all threads (default: unresolved only)
- `--unanswered`: threads where PR author has not replied last
- `--since DURATION`: relative time filter (e.g. `1h`, `2d`, `1w`)
- `--no-bots`: drop bot comments entirely (default: sanitize and keep)
- `--max-body N`: cap comment body length (default: 500)

Bot comments are sanitized by default: HTML details blocks, HTML comments, decorative separators are
stripped, then truncated to `--max-body`. Pass `--no-bots` to drop them entirely.

## Pending Review Workflow

### Check for existing pending review

```sh
gh-review view owner/repo 42
```

If a pending review exists, the output shows a `PENDING REVIEWS` section with `PRR_...` IDs.

### Start a pending review

Only if no pending review exists.

```sh
gh-review start owner/repo 42
```

Output:

```txt
id: PRR_kwDOAAABbcdEFG12
state: PENDING
```

### Add comment (single line)

```sh
gh-review comment owner/repo 42 \
  --review-id PRR_kwDOAAABbcdEFG12 \
  --path internal/service.go \
  --line 42 \
  --body "nit: prefer helper"
```

### Add comment (multi-line)

The `--line` is the end line; `--start-line` is the beginning.

```sh
gh-review comment owner/repo 42 \
  --review-id PRR_kwDOAAABbcdEFG12 \
  --path internal/service.go \
  --start-line 10 \
  --line 15 \
  --body "Extract this block into a helper"
```

Optional flags: `--side LEFT|RIGHT` (default RIGHT), `--start-side LEFT|RIGHT`.

### Delete a pending review

```sh
gh-review delete PRR_kwDOAAABbcdEFG12
```

## Replying to Comments

Use `gh-review reply` to reply to existing comment threads. It auto-detects whether the comment is a
review thread or conversation comment and routes to the correct API.

```sh
gh-review reply owner/repo 42 COMMENT_ID --body "Fixed in abc123."
```

The `COMMENT_ID` is the numeric database ID shown as `#ID` in `view` output comment headers (e.g.
`@reviewer (2026-05-14) #98765:`). Extract the number after `#` from the comment you want to reply
to.

## Line Targeting Constraints

GitHub's API only supports comments on lines within diff hunks (changed lines plus a few lines of
surrounding context). Lines in the gap between hunks cannot be targeted.

When `comment` targets a non-diff line, it exits non-zero with:

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

- `PRR_...`: Review node ID (from `start` or `view`)
- `PRRT_...`: Thread node ID (from `comment` or `view`)

## Output

- Plain text prose, not JSON (optimized for LLM consumption)
- Errors go to stderr with non-zero exit
