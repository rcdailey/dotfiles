---
name: gh-pr-review
description: >-
  Use when reading, posting, or managing PR review comments via the `gh-review` tool: viewing
  PR comments with filtering, leaving inline comments on specific diff lines, starting or
  deleting pending reviews, replying to review threads, editing or removing individual review
  comments. Triggers on phrases like "review this PR", "check for comments", "leave a comment
  on line X", "add review feedback", "start a pending review", "reply to the comment", "edit
  the comment", "remove that comment", "delete that comment", "fix my comment", "move comment
  to line X", or any task involving PR comments and code review. Do NOT use for merging,
  approving via `gh pr review --approve`, or non-review PR operations.
---

# PR Review

All PR comment operations (reading, writing, replying) MUST go through `gh-review`. Do NOT use raw
`gh api` or `gh pr` for any review-related task. Run `gh-review --help` and `gh-review <command>
--help` for authoritative syntax; this skill covers workflow and semantics only.

## Critical Rules

- NEVER submit reviews. The user manually submits pending reviews via GitHub UI.
- All new review comments MUST go through a pending review. Never post comments directly.
- When a line target is outside diff hunks, `comment` automatically retries as a file-level comment
  on the same file. The output includes a `note:` line indicating the fallback. No manual retry or
  relocation needed.

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

## Editing and Removing Comments

`gh-review edit` modifies an existing review comment. Two paths depending on what changed:

- **Body only** (no positioning args): patches the comment in place. One API call.
- **Repositioning** (any of `--path`, `--line`, `--start-line`, `--side`, `--start-side`): deletes
  the old comment and creates a new one on the same pending review. Requires `--review-id`. Omitted
  fields are merged from the current comment.

`gh-review remove` deletes a single review comment.

Both commands take the comment node ID (`PRRC_...` from `comment` output's `comment-node-id` field).
These commands operate on pending review comments only; published comments should be edited through
the GitHub UI.

## Line Targeting

GitHub's API only supports line-level comments on lines within diff hunks (changed lines plus
surrounding context). Lines in the gap between hunks cannot be targeted as line comments.

When `comment` targets a non-diff line, it automatically falls back to a file-level comment on the
same file (using `subjectType: FILE`). The output includes a `note:` field explaining the fallback.
The comment still lands on the correct file; it just appears at the top of the file's diff rather
than on a specific line.

To post a file-level comment directly (skipping the line attempt), omit `--line`:

```bash
gh-review comment --review-id PRR_... --path {file} --body '{body}'
```

**Suggestion blocks:** Suggestions only work on line-level comments. The `--start-line` to `--line`
range defines what GitHub replaces when a suggestion is applied. The range MUST exactly match the
lines being replaced. Do NOT include surrounding context lines in the range; they will be deleted.

## ID Formats

- `PRR_...`: Review node ID (from `start` or `view`)
- `PRRT_...`: Thread node ID (from `comment` or `view`)
- `PRRC_...`: Comment node ID (from `comment` output's `comment-node-id` field); used by `edit` and
  `remove`
- `#NNN`: Numeric database ID (from `view` output or `comment` output's `comment-id` field); used by
  `reply`
