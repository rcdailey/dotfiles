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
`gh api` or `gh pr` for any review-related task. Run `gh-review --help` and `gh-review <command>
--help` for authoritative syntax; this skill covers workflow and semantics only.

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

## Pending Review Workflow

1. `gh-review view` the PR. If the output includes a `PENDING REVIEWS` section, reuse that `PRR_...`
   ID. Otherwise, `gh-review start` to create one.
2. `gh-review comment` for each inline comment, passing the review ID.
3. Stop. The user submits the review manually via the GitHub UI.

To discard a pending review: `gh-review delete PRR_...`.

## Replying to Comments

`gh-review reply` posts to an existing thread. It auto-detects whether the target is a review thread
or conversation comment and routes to the correct API.

The `COMMENT_ID` argument is the numeric database ID shown as `#ID` in `view` output headers (e.g.
`@reviewer (2026-05-14) #98765:`). Extract the number after `#`.

## Line Targeting

GitHub's API only supports comments on lines within diff hunks (changed lines plus surrounding
context). Lines in the gap between hunks cannot be targeted.

When `comment` targets a non-diff line, it exits non-zero. When this happens:

1. Continue posting remaining comments that target valid lines.
2. After all comments are posted, report the failures to the user with file, line, and the intended
   comment body so they can post manually.

**Suggestion blocks:** The `--start-line` to `--line` range defines what GitHub replaces when a
suggestion is applied. The range MUST exactly match the lines being replaced. Do NOT include
surrounding context lines in the range; they will be deleted.

## ID Formats

- `PRR_...`: Review node ID (from `start` or `view`)
- `PRRT_...`: Thread node ID (from `comment` or `view`)
