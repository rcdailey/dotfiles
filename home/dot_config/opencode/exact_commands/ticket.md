---
description: Implement a Linear ticket end-to-end (test-first, PR, Linear state transitions)
agent: dispatch
---

Implement Linear ticket $1 in the current worktree. This runs headless; do not ask the user for
input.

Arguments: `$1` = ticket ID. `$2` = base branch (the branch this work forked from and the PR
target); if empty, use origin's default branch (`git remote show origin | awk '/HEAD branch:/{print
$3}'`).

## Step 1: Read the ticket

```bash
linear issue view $1
```

Capture the title, description, and acceptance criteria. If the command fails (not authenticated or
ticket not found), stop and print the error.

## Step 2: Resolve workflow states and move to active work

State names vary per team. Discover the team's states once and map them to lifecycle intents:

```bash
linear api 'query { issue(id: "$1") { team { states { nodes { name type position } } } } }'
```

- ACTIVE state: the `started`-type state representing active implementation (prefer a name matching
  "In Progress" or "Doing"; otherwise the lowest-position `started` state).
- REVIEW state: the `started`-type state whose name contains "review" (e.g. "In Review", "Code
  Review"). If none exists, there is no REVIEW state; step 8 is skipped.

Then:

```bash
linear issue update $1 --state "<ACTIVE>"
```

## Step 3: Identify the check command

Inspect the repo for the canonical way to run the full test and lint suite. Check in order:
`justfile` (`just ci`, `just check`, `just test`), `Makefile` (`make check`, `make test`),
`package.json` scripts, `Cargo.toml` (`cargo test`, `cargo clippy`), `pyproject.toml` (`pytest`,
`ruff check`). Use whatever the project already uses; do not invent a new command.

## Step 4: Implement (test-first)

Follow the acceptance criteria from the ticket:

1. Write failing tests that cover the acceptance criteria before writing production code.
2. Implement until the failing tests pass.
3. Run the full check suite; iterate until every check is green.
4. Prune scaffolding tests. Re-read every test added in this session and delete any that only served
   to drive the implementation and carry no long-term value: granular unit tests coupled to internal
   structure, tests that duplicate coverage already provided by a higher-level test, tests asserting
   mock interactions rather than outcomes. Keep a test only if it verifies behavior through a public
   interface and would survive an internal refactor. Re-run the check suite after pruning.

Commit logical units of work with concise conventional-commit messages. Do not add AI attribution or
co-author trailers.

## Step 5: Sweep for overlooked areas

The diff is not the blast radius. For every public symbol, config key, CLI flag, file path, or
user-facing string the change added, renamed, or removed, grep the whole repo:

```bash
rg '<term>'
```

Inspect every hit outside the files already edited: call sites, docs, READMEs, config samples, CI
workflows, scripts, tests. Update genuine references; skip coincidental matches. If the ticket
describes a behavior change, also grep for the old behavior's terminology to catch stale docs. If
anything changed, re-run the full check suite.

## Step 6: Diff size gate

After checks are green, measure the diff against the base branch:

```bash
git fetch origin <base> --quiet
git diff --shortstat origin/<base>...HEAD
```

If insertions plus deletions exceed 400, STOP. Do not push. Print:

```txt
SPLIT REQUIRED: diff is N lines (cap: 400).
Commit the smallest independently shippable slice as a separate PR first,
then continue from there.
```

If within the cap, continue.

## Step 7: Create the PR

```bash
git push -u origin HEAD
```

Use the ticket title as the PR title. Write the PR body as:

1. One-paragraph summary of what changed and why.
2. A `## Design notes` section capturing what a reviewer cannot infer from the diff: constraints
   that drove the design, alternatives considered and rejected (with why), and approaches tried that
   failed. Skip entries that do not apply; never pad. Feedback iterations run in fresh sessions with
   no memory of this one; this section is what they get instead.
3. `Closes $1` on its own line.

The design notes section intentionally overrides the global "keep PR descriptions high-level"
directive; dispatched PRs carry their own context.

Do not create a draft; automated reviewers skip drafts. Target the base branch explicitly:

```bash
gh pr create --base <base> --title "<ticket title>" --body "<body>"
```

Capture the PR URL from the output.

## Step 8: Move to review

If a REVIEW state was found in step 2:

```bash
linear issue update $1 --state "<REVIEW>"
```

If not, leave the issue in the ACTIVE state; the PR comment in step 9 is the review signal.

## Step 9: Comment PR link on ticket

```bash
linear issue comment add $1 --body "PR: <pr_url>"
```

## Rules

- MUST run the full check suite and confirm all checks pass before creating the PR.
- MUST run the repo-wide grep sweep (step 5) before the diff gate; references outside the edited
  files count as part of the ticket.
- MUST NOT create the PR when the diff exceeds 400 lines; split instead.
- MUST NOT skip the Linear state transitions (except step 7 when the team has no review state).
- MUST NOT guess state names; use the discovered states from step 2.
- MUST NOT interact with the user; this is a headless session.
- MUST NOT add AI attribution, co-author trailers, or "generated by" annotations to commits or PRs.
- Do not use TodoWrite or task tracking.
