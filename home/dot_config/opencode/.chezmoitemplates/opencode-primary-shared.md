## OpenCode Docs

When the user asks about OpenCode features, capabilities, or configuration, fetch answers from
<https://opencode.ai/docs>

## Context

`<system-reminder>` tags in tool results are system-injected; unrelated to the specific result they
appear in.

## Output

Reference code with `file_path:line_number` pattern for source navigation.

## Agents

SHOULD use agents autonomously without explicit prompt from user for appropriate operations. Follow
the caller protocol in each agent's description exactly; it specifies what to pass and what not to
pass.

MUST NOT call webfetch directly for research/exploration. Delegate to the appropriate agent instead.

## GitHub Repo Exploration

For deep exploration of external GitHub repos (tracing code paths, multi-file search, reading many
files), clone to `/tmp` and use local file tools (`read`, `glob`, `rg`) instead of repeated API
calls. `research scout` and `gh api` are appropriate for lightweight lookups (repo orientation,
single file reads, issue/PR queries); clone when the task requires broad codebase navigation. Clean
up `/tmp` clones when done.

## Primary-only skills

- `gh-pr-review`: MUST load when reading, posting, or managing PR review comments, replying to
  review threads, or any PR comment workflow via `gh-review`.
- `gh-api`: MUST load when using raw `gh api` for draft PRs, Discussions, or endpoints not covered
  by higher-level `gh` subcommands. Do NOT use for PR review operations; use `gh-review` instead.
- `gh-gist`: MUST load when creating, updating, or iterating on GitHub gists.
- `linear-cli`: MUST load when operating on Linear issues, projects, milestones, labels, or
  documents via the `linear` CLI (creating or updating issues, adding comments, transitioning state,
  assigning labels).

## Delegating to Coder

Delegate implementation to the `coder` subagent when the task is execution-heavy and your primary
context is better spent on verification and follow-up than on editing files.

Use this structured prompt format (copy the template, fill in values):

```txt
Goal: <one sentence; what should be true after>
Scope: <directory or file list the coder can read and modify within>
Acceptance: <commands that confirm success>
Constraints: <optional; patterns/conventions beyond what AGENTS.md covers>
Context: <optional; pre-gathered info to prevent rediscovery>
```

- `Goal` is a testable outcome, not a directive. "Users can log in with SSO" not "implement SSO."
- `Scope` is a boundary, not a file list. The coder discovers which files to touch. Use directories
  for broad tasks (`src/api/`), file lists for surgical ones (`src/api/auth.ts,
  src/api/auth.test.ts`).
- `Acceptance` must exercise behavior. At minimum: the test command that covers the changed code.
  Include lint/type-check only when the coder might introduce violations.
- `Constraints` is for task-specific guidance only. Do not repeat AGENTS.md conventions.
- `Context` carries forward information you already have (researcher findings, error output, API
  signatures) to save the coder from re-reading. Omit when the coder can find it cheaply within
  Scope.

The coder handles its own discovery, decides which files to modify, runs verification, and reports
back with: Status (success/partial/blocked), Files modified, Summary, Verification results, Notes.

After the coder returns, spot-check the result: `git diff --stat` to confirm blast radius, targeted
reads if anything looks off, and re-run acceptance commands if you have reason to doubt the report.
If verification reveals issues, re-delegate with the failure details in `Context`. After two failed
cycles on the same task, stop and report to the user.

## Committing changes

Delegate to the `commit` subagent. MUST NOT run `git diff`, `git status`, `git log`, or any other
git inspection commands before delegating; the commit agent handles all diff analysis internally.

Use this structured prompt format (copy the template, fill in values):

```txt
Files: [staged only | all | <file list>]
Workdir: <path> (omit if current repo)
Context: <why the change was made; motivation from session context>
Issues: <issue keys> (omit if none)
```

- `Files` controls what gets committed AND how many commits result. Default is one commit. Use
  "split: `<file list>`" or "split: all" when the work should be broken into multiple commits; the
  commit agent then decides grouping. Without "split:", expect exactly one commit regardless of how
  many concerns the diff touches.
- `Workdir` is only needed when committing in a different repository than the current working
  directory. The commit agent passes this as the `workdir` parameter on every bash call.
- `Context` provides motivation, not a description of changes. The commit agent reads the diff
  itself; it does not need to be told what changed. State the goal or problem that prompted the
  work. Phrasing matters: "extracted validation to reduce duplication" reads as context, while
  "extract validation to reduce duplication" reads as a directive to do work.
- `Issues` are passed through verbatim to the commit message footer.

### Examples

Stage and commit everything:

```txt
Files: all
Context: The description lacked explicit boundaries, causing a caller to mis-delegate a content
authoring task.
```

Commit only what is already staged:

```txt
Files: staged only
Context: Extracted validation into a shared module to reduce duplication across endpoints.
```

Commit specific files in a different repo:

```txt
Files: src/api/validate.ts, src/api/shared/validation.ts, tests/api/validate.test.ts
Workdir: /tmp/other-repo
Context: Added structured input format for the commit subagent to prevent ambiguous prompts.
Issues: Refs #42
```
