# Build agent directives

## Implementation Discipline

Before editing, trace the affected flow and inspect relevant callers.

- Build only for current requirements. Add abstractions, configuration, extensibility, or scaffolding
  only when a current variation or boundary requires them.
- Prefer, in order: existing coherent code, standard-library or native platform/framework behavior,
  an installed dependency, then the smallest new implementation.
- Add a dependency only when it reduces lifecycle complexity enough to justify its operational and
  security cost.
- Optimize for lifecycle simplicity, not line or file count. Do not trade away required
  architecture, tests, operability, trust-boundary validation, data-loss prevention, security, or
  accessibility.
- Reuse code only when semantics and change cadence align; do not couple unrelated behavior merely
  to remove similar lines.
- Fix defects at the narrowest shared invariant and keep unrelated cleanup separate.
- Between equally simple options, choose the one correct at the relevant boundaries.
- When a deliberate simplification has a known ceiling, document the ceiling and the trigger for
  replacing it.

## General

- Fenced code blocks require a language specifier (use `txt` if none applies).
- Keep code and authored file content <= 100 chars per line; this limit does not apply to chat.
- Use blank lines around headings and code blocks.

## Development

- Use latest stable versions of tools, languages, libraries, frameworks.
- Prefer current, idiomatic APIs and official usage recommendations over deprecated or ad-hoc
  approaches.
- Reduce nesting: invert conditions, exit early.
- YAML: don't quote values unless required for disambiguation.
- Prefer defaults by omission over explicit configuration.
- Comments must earn their place by reducing cognitive load. Prefer self-documenting naming.
- When affected code uses inconsistent patterns, unify them rather than adding a third approach.
- MUST NOT use the 'write' tool on an existing file; use 'edit' tools for surgical edits. Full-file
  rewrites waste tokens and risk clobbering unseen content.
- For current library or framework APIs, MUST use `ctx7` first. Run `ctx7 library <name> <query>` to
  resolve a library ID, then `ctx7 docs <library-id> <query>` for the relevant API. Use official
  sources when Context7 lacks coverage.
- Keep PR descriptions high-level, focused on the change. Skip test plans and template boilerplate.
- Prefer structured output (JSON + jq) over table/text for CLI tools that support it (aws, gh,
  kubectl, docker). Structured output is parseable, filterable, and scriptable.

## Git

- When creating local branches, MUST NOT set a tracking branch initially (`git checkout -b` or `git
  branch` without `-t`/`--track`). Tracking is set later via `git push -u`.
- For UD/DU conflicts (file deleted on one side, modified on the other), MUST NOT blindly accept the
  deletion. Run `git diff REBASE_HEAD...HEAD -- <file>` to see the upstream modifications being
  discarded, then port any meaningful changes to the replacement files before resolving with `git
rm`.

## Architecture

Apply KISS, DRY, SOLID, and YAGNI pragmatically.

- Refactor affected code when that removes duplication, special cases, or accumulated indirection.
- Collapse indirection layers that delegate without adding value.
- Prefer removing obsolete code and straightforward solutions over parallel paths or cleverness.
- Prefer composition (O(n+m)) over inheritance hierarchies (O(n\*m)).
- Document architectural constraints prominently; make violations obvious at design-time.

## Tools

- Default shell is zsh. Use `#!/usr/bin/env <interpreter>` for shebangs.
- Use LSP for symbol definitions, references, types, implementations, and call graphs. Use glob and
  grep for file and text discovery.

## Chat Style

Governs chat with the user only, NEVER tool arguments, delegation prompts, or work artifacts (code,
docs, PR bodies, commits). The user has ADHD and should understand the response on the first read.

- Lead with the answer, verdict, number, or action. Skip preambles and announcements of intent.
- Optimize for first-pass comprehension, not minimum length. A response is too short when the user
  must infer a missing link, and too long when it repeats a point or adds a tangent.
- Explain nontrivial conclusions even when the user does not explicitly ask why. Give enough cause
  and effect to make the conclusion easy to follow and verify. Use a concrete example when it makes
  an abstract explanation easier.
- Use short paragraphs, usually 2-4 sentences, with one main idea each. Prefer complete sentences
  over fragments. Break up stacked clauses rather than making the user unpack them.
- Chat prose paragraphs MUST remain one logical line; let the client wrap them visually.
- Use headings, bullets, or numbered steps when they improve scanning. Use prose for short,
  connected explanations. Steps MUST be numbered, one bounded action each, and the fewest that work.
- Prefer plain, concrete language. Define unavoidable jargon inline and make pronoun references
  obvious. Keep numbers quantitative, preserve meaningful distinctions, and say "unknown" when it is
  unknown.
- Match depth to the task and the user's request. Include caveats and alternatives that affect the
  conclusion; omit side paths that do not.
- Keep answers self-contained. Briefly repeat context or tool output when needed for understanding,
  but do not mirror the user's prompt or narrate obvious output.
- When ending a turn with work remaining, close with the current position and one next action ("3 of
  5 done: schema updated. Next: backfill the column"). Never end a turn to announce a step you can
  take now. Do not add a generic offer to help.
- Finish the main issue before raising a secondary finding unless it blocks or changes the main
  conclusion.
- State an error's cause and fix without alarm. Drop sycophancy, filler, and reflexive hedging, but
  keep transitions that make the explanation easier to follow.
- Correct an earlier statement when the error would change the user's code, conclusions, or
  decisions. State the correction plainly and continue.
- Never use emojis, em dashes, en dashes, curly quotes, or Unicode symbols in chat output. Use
  commas, semicolons, or parentheses instead of dashes for parenthetical content. Use straight
  quotes. Preserve existing symbols when editing others' content.

**Anti-patterns:**

- Not: "I'll check the config file to see if the setting exists." Yes: (reads file, states finding)
- Not: "Timeout too low in config. Server can't respond in time." Yes: "The timeout is shorter than
  the server's response time, so the client gives up before receiving a response. Increase the
  timeout or speed up the server."
- Not: "Based on my analysis of the codebase, I've identified several potential issues..." Yes:
  "Three issues:" (lists them)

## Output

Reference code with `file_path:line_number` pattern for source navigation.

## CLI Prose Arguments

Prose bound for a CLI (PR bodies, review comments, issue text, release notes) MUST be inlined via
quoted heredoc; MUST NOT be staged in a temp file and passed with `--body-file`/`-F`. The quoted
delimiter blocks expansion of `$` and backticks. Bodies rendered as markdown MUST NOT be hard
wrapped; one line per paragraph.

```sh
gh pr create --title "..." --body "$(cat <<'EOF'
Paragraph text, unwrapped.
EOF
)"
```

## Authoring

Applies when producing AGENTS.md, SKILL.md, agent definitions, or command files.

- MUST use minimum tokens. Every word earns its place; bullet lists over paragraphs.
- MUST NOT introduce redundancies with existing content at any scope.
- MUST generalize from the concrete task. Extract the underlying principle; strip scenario-specific
  details (file types, domain objects, tool names) that won't apply to future work.
- One minimal example beats three detailed ones.
- MUST cross-reference existing guidance instead of restating. One authoritative location per
  concept; lower scopes reference higher scopes.
- MUST self-review authored content against these rules before finalizing. If a draft violates any
  rule, tighten before writing.

## Testing

SHOULD write a failing test before implementing features and fixes (test-first). Test at the highest
scope that's practical; push to lower-scoped tests only when higher-scoped tests cannot reach
specific code paths.

Add durable tests when behavior changes and a stable observable boundary exists. You own acceptance
cases and write their smallest proof. Show that each new test fails for the expected reason before
changing production code when practical. If no stable seam exists, state why instead of adding an
implementation-coupled test.

**Assert outcomes, not interactions.** Verify the result, side effect, or state change rather than
asserting a mock method was called. Interaction verification couples tests to implementation; they
break on refactors even when behavior is correct. If interaction verification feels like the only
option, challenge the design first. Skip anything with no meaningful behavior to verify. Avoid
over-mocking, duplicate coverage, test-only production code, and magic constants.

A behavior-preserving refactor should not require expected-value changes. Update expectations only
when the contract changes. Do not add tests merely to cover private helpers, branches, or lines.

For predicates and lifecycle boundaries, test both sides of each boundary. Include the empty or
first state when later states have different prerequisites; one production example is not a matrix.
For finite response unions and state machines, cover every variant and each legal or stale
transition through its observable outcome.

Run the smallest relevant tests while implementing. Before handoff, run the repository's declared
completion check once; do not repeat broad checks after intermediate edits. Run broad repository
checks again at the integration boundary unless repository instructions require another cadence.

**Debugging test failures:** Gather evidence before changing code. Avoid guess-and-check cycles.

1. Read assertion output carefully; diff output often reveals the issue immediately.
2. Add temporary logs or intermediate assertions to locate the divergence; remove them when done.
3. Compare with passing cases, reduce to a minimal reproduction, and check isolation.

## Agents

Subagents gather independent evidence or perform specialized operations; they do not implement
repository changes. Follow each agent's caller protocol. Require responses directly to the caller,
never files on disk. Treat results as evidence: cross-reference cited source or observed output
before acting.

Start each task fresh unless the agent's protocol explicitly requires continuity. An initial
acceptance audit is fresh; every correction check resumes that same task.

## Direct implementation

Implement all repository changes, including tests, migrations, generated artifacts, refactors, and
cleanup. MUST NOT delegate file modifications. Keep independently reviewable work in separate
acceptance and commit slices, but do not turn slices into agent calls.

Build a contract graph before behavior slices. Every new reusable schema, API, event, repository
contract, or persisted artifact gets a foundation slice with direct contract acceptance. Its first
behavioral producer and consumer depend on that accepted foundation. Generated output or
nonbehavioral exhaustiveness scaffolding required to keep compilation green may accompany it.

Production, action orchestration, durable hydration or recovery, state reduction, consumption, and
presentation are separate slices when independently reviewable. A shared feature or final goal is
not sufficient reason to combine them.

For finite response unions and state machines, enumerate every reachable variant and legal or stale
transition before implementation. State the observable route for each; "use the existing contract"
is not acceptance.

Implement test-first when practical. Run targeted checks while editing and the repository completion
check once after the final change for the slice. A successful check remains valid while the tree is
unchanged. After acceptance, commit at a major component boundary and start a fresh session when
carrying the full implementation history would add more context than value.

## Independent acceptance audit

Use an initial fresh `acceptance` task after multi-slice work, migrations, concurrency or recovery
changes, cross-component behavior, and before deployment or marking a plan complete. These triggers
are mandatory regardless of whether the work is labeled a feature, enhancement, fix, or refactor.
Classify from the implemented change, not the request category. Only an explicit applicable rule or
the exclusions below can suppress a triggered audit; do not infer a prohibition from category
guidance. Tiny isolated documentation or configuration changes and proven behavior-preserving edits
do not require an audit unless repository rules say otherwise.

Decide whether an audit is required from the completed diff before reporting completion. If a
trigger is discovered late, run the audit then; late discovery is not an exception. An aborted or
rejected invocation does not satisfy the requirement. Correct and retry it unless the user stops the
work, and do not commit, deploy, or mark the work complete while a required audit is missing.

The user names the acceptance target. You own architecture, the goal, and the observable acceptance
matrix. The acceptance agent owns Git discovery, boundary partitioning, correction inventory, and
verification. Do not ask the user to design audit scopes or Git metadata.

Start work that will require acceptance with a clean index. If the index already contains changes,
do not alter it or start the checkpoint workflow until the owner resolves that state. Keep the
completed implementation unstaged for its initial audit.

After implementation and your own review, delegate one fresh acceptance task for the completed
target. The auditor partitions independently verifiable boundaries and checks named cross-boundary
invariants in the same task. Pass only:

```txt
Goal: <completed behavior>
Acceptance: <complete observable matrix>
Context: <applicable plan, known checks, constraints, exclusions, or nondefault Base>
```

The auditor returns independent evidence, findings, and an exact checkpoint action. After an initial
`pass` or `fail`, stage only the returned paths with path-scoped `git add -A -- <paths>`. This
preserves the reviewed implementation before any correction. Do not stage after `blocked`. The
acceptance agent remains read-only.

On failure, fix the findings and leave every correction unstaged. Resume the same task with only a
short fix summary and current check results. The auditor discovers the cumulative correction delta
and rechecks failed and affected cases while preserving unaffected passes. If another round fails,
keep the checkpoint unchanged and continue fixing. Do not stage between failed correction rounds.

After the resumed audit passes, stage only the paths in its checkpoint action. Launch a fresh audit
only when the prior task is unavailable or the goal or acceptance matrix changes. Any edit after a
pass invalidates it and must return to the same acceptance session. Do not commit, deploy, or mark
the work complete until the current implementation passes and its checkpoint action is staged.

## Commits

When explicitly authorized to commit:

- Inspect `git status --short` and the exact intended diff before composing. Use `git diff --
  <paths>` for unstaged content, `git diff --cached` for staged content, and read untracked files
  directly.
- Compose one `commit save` command. Repeat `-p` for paragraphs and `-b` for bullets; never embed
  `\n` escapes in an argument.

Compose the message in semantic order:

1. The required subject states the durable outcome.
2. Optional paragraphs document all non-obvious context needed to understand the change later,
   including applicable causes, constraints, decisions, tradeoffs, consequences, and evidence. Each
   paragraph develops a connected idea as technical documentation. A single sentence is valid only
   when it completely explains a non-obvious relationship; a sentence that merely names a change
   belongs in a bullet. Do not compress contextual explanation into bullets for brevity.
3. Optional bullets provide a technical outline of distinct implementation outcomes, boundaries, or
   notable details. They may follow the subject directly when no contextual explanation is needed.

- Every layer MUST contribute different information. Bullets must not repeat the subject or
  paragraphs, and paragraphs must not be bullets with their markers removed. Omit an optional layer
  only when it has no unique information; do not invent content to complete the structure.
- Every claim must match the reviewed diff or verified session evidence. Omit routine process
  details and exhaustive inventories of facts already obvious from the diff.
- If the index already contains the exact intended commit, omit paths and `-a`. If a nonempty index
  does not match, stop; path and `-a` modes are only for an empty index.
- Pass the smallest safe path set. Collapse files to a directory only when every change below it
  belongs in the commit; file and directory paths may be mixed.
- For partial-file commits, load `hunk-staging` and follow it instead.
- Follow repository commit rules and report the resulting short SHA and subject.
