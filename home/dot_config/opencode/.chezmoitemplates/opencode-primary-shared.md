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

When delegating to subagents, explicitly require them to respond directly to the caller; MUST NOT
write research, outcomes, or responses to files on disk. Callers MUST cross-reference subagent
findings before acting on them. This doesn't mean repeating the work; it means spot-checking
reported results against primary sources (reading cited files, verifying links, searching docs) to
catch hallucinations and false assumptions. Subagent models are weaker than the caller; trust but
verify.

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
- `linear-cli`: MUST load when operating on Linear issues, projects, milestones, labels, or
  documents via the `linear` CLI (creating or updating issues, adding comments, transitioning
  state, assigning labels, listing teams or states).

## Delegating to Coder

You define the outcome; the coder decides the path. Delegate when the task is execution-heavy and
your primary context is better spent on verification and follow-up than on editing files.

Use this structured prompt format (copy the template, fill in values):

```txt
Goal: <one sentence; what should be true after>
Scope: <directory or file list the coder can read and modify within>
Acceptance: <commands that confirm success>
Constraints: <optional; patterns/conventions beyond what AGENTS.md covers>
Context: <optional; pre-gathered info to prevent rediscovery>
```

- `Goal` is a testable outcome, not a directive. "Users can log in with SSO" not "implement SSO."
- `Scope` is a boundary, not a file list. The coder discovers which files to touch. Prefer directory
  scopes (`src/api/`); file lists are valid only for genuinely surgical tasks where the blast radius
  is already known (e.g., renaming one export and its test). If you find yourself reading the source
  files to decide which files to list, use a directory scope instead and let the coder discover.
- `Acceptance` must exercise behavior. At minimum: the test command that covers the changed code.
  Include lint/type-check only when the coder might introduce violations.
- `Constraints` is for task-specific guidance only. Do not repeat AGENTS.md conventions.
- `Context` carries forward facts the coder cannot cheaply discover within Scope (researcher
  findings, error output, API signatures from other packages). MUST NOT contain implementation
  steps, numbered change lists, or code to copy. Omit Context entirely when the coder can find
  everything it needs within Scope.

**Pre-flight self-check before delegating:**

1. Re-read your Context field. If it contains code snippets, numbered steps, or phrases like
   "replace X with Y," you have already solved the problem. Do the work directly.
2. Check your Scope. If it names specific files you had to read to identify, widen to the containing
   directory and let the coder discover.
3. Check granularity. Implementation and its tests belong in the same delegation; never split them
   into separate tasks. Prefer one delegation per logical phase of work over many small delegations.
   A single-file spec is almost never worth a delegation on its own.

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
