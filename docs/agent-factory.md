# Agent factory plan

Status: rung 1 in progress. Testbed: recyclarr.

A staged plan for moving from interactive TUI sessions to supervised, ticket-driven agent workflows
on a local workstation. Each rung removes one piece of manual involvement; the climb stops wherever
trust runs out. This file is the living version of the plan; iterate here.

## Background

- OpenCode provides the automation surface: `opencode serve` (HTTP API: sessions, prompts, SSE event
  bus), `opencode run` (headless CLI; `--command`, `--session`, `--attach`), plugin hooks
  (`session.idle`, `permission.asked`). Experimental worktree API exists behind
  `OPENCODE_EXPERIMENTAL_WORKSPACES` but plain `git worktree` is fine.
- Community-converged pattern matches this design: one worktree (or container) per task,
  auto-confirm permissions, PR-comment iteration for feedback. Local tools in this space
  (claude-squad, uzi, container-use) are thin wrappers over the same primitives.
- Review practice in the field is risk tiering, not blanket trust or full line-by-line review:
  auto-merge for docs/deps with green CI, AI review plus human skim for routine logic, full human
  review for auth/payments/migrations/concurrency, pair review for novel architecture.
- Known agent failure modes to design against: happy-path bias, missing security context, bad
  dependency choices, concurrency bugs, cross-session architecture drift, tests that assert the
  implementation instead of behavior.
- Auth constraint discovered early: Anthropic prohibits subscription OAuth (Pro/Max) for
  automated/headless services and enforced this in Jan 2026; tokens also expire too fast for
  unattended pods. Any future containerized factory runs on `ANTHROPIC_API_KEY` and per-token
  billing. Budget accordingly.

## Workflow rules

- The unit of work picks the workflow, not the repo. Hand-driven TUI sessions keep committing to
  main (review happened synchronously). Dispatched tickets always go through a branch and PR (review
  happens asynchronously).
- Tickets exist only as dispatch fuel. No ticket regime for interactive work.
- Solo repos: no branch protection or required approvals. The PR is an inspection surface, not a
  gate; merge stays one keystroke after a green skim.

## Rung 1: supervisor ergonomics (current)

You trigger everything, you review everything. The deliverable is calibration, not automation: after
~10 tickets, know the agents' failure patterns, the ticket-writing quality bar, and whether PRs
deserve a lighter touch.

Artifacts (all in this repo):

1. `home/dot_config/opencode/exact_commands/ticket.md`: slash command holding the dispatch prompt
   template (read Linear ticket, move to In Progress, implement test-first, run checks until green,
   repo-wide grep sweep for overlooked references, push, `gh pr create`, move to In Review, comment
   PR link, ~400 line diff cap with split-and-stop escape hatch). This template is where supervision
   lives; iterate on it after every dispatched ticket.
2. `home/dot_config/exact_zsh/functions/dispatch`: worktree add + tmux window + `opencode run
   --command ticket <ID>`. Companion `dispatch-done` removes the worktree and kills the window.
3. `home/dot_config/opencode/exact_plugins/notify.ts`: `notify-send` on `session.idle`, only for
   dispatched sessions (gated on `OPENCODE_DISPATCH=1`, set on the tmux window by `dispatch`) and
   only for top-level sessions (subagent idles are skipped via `parentID`).
4. `home/dot_config/opencode/exact_commands/pr-feedback.md`: slash command for feedback iterations,
   covering both review comments and CI failures. Checks `gh pr checks` and pulls failing run logs
   (`gh run view --log-failed`); fixes failures caused by the PR, reruns flaky checks once, and
   comments on the PR when a failure isn't addressable from the branch. Reads unresolved PR comments
   (`gh-review view`), triages rather than obeys (bot nitpicks get evaluated; disagreements get a
   reply explaining why, never a silent skip), fixes, pushes, replies to each comment with what was
   done. Works in the original session (`--session <id>`) or fresh (reads the PR diff first; rung 2+
   won't always have the session).
5. CodeRabbit GitHub App on recyclarr (full Pro tier is free for public repos). Supplements, not
   replaces, the human pass at this rung. Tune `.coderabbit.yaml` early; expect most comments to be
   nitpicks and tune until the signal is worth reading.

Daily flow: write/refine tickets in Linear (`to-issues`), `dispatch ENG-123`, keep doing interactive
work, get notified, wait for CI + CodeRabbit, review the PR line-by-line as today. Feedback goes on
the PR as review comments, then one trigger from the ticket's tmux window: `opencode run --session
<id> --command pr-feedback <PR>`. The same trigger handles red CI runs; the command picks up failing
checks even when there are no comments. Trivia gets fixed by hand. Merge, `dispatch-done`, then
record what the ticket template should have said to prevent whatever went wrong.

The human review pass stays full-depth until CodeRabbit's findings demonstrably overlap with it
(roughly a dozen PRs of evidence); only then does the human pass demote to a skim.

Testbed order: recyclarr first (Linear project exists, extensive CI, public OSS repo where PRs are
normal). home-ops second (already bot-PR native via Renovate + flux-local; homelab work is often
well-specified). chezmoi stays interactive (small personal changes needing taste; bad ROI for
ticket-writing).

Explicitly out of scope at this rung: Linear polling, auto-dispatch, automatic CI/comment routing
(the human reads and triggers `pr-feedback`), permission auto-answering.

## Rung 2: the dispatcher

A daemon (Python CLI under `scripts/`, matching the existing uv + Click pattern) that makes ticket
assignment the event:

1. Poll Linear for issues in a designated state ("Agent Ready")
2. Per issue: worktree + branch, create session against long-running `opencode serve`, send the
   ticket as the prompt
3. Watch SSE for `session.idle`; verify a PR appeared; move ticket state; notify
4. Auto-answer permission asks (worktree isolation limits blast radius)

Human still reviews every PR. The `dispatch` function from rung 1 is the core of this daemon;
polling replaces typing it, SSE replaces checking on it.

## Rung 3: the feedback loop

After PR creation the dispatcher polls CI status and review comments (`gh pr checks`, `gh-review
view`). On failure or feedback it resumes the same session with the details and lets the agent
iterate until green. Tickets land in "Ready for human review" only when checks pass.

## Rung 4: shrink the human review

Add an automated review pass on every agent PR (PR-Agent is the no-subscription option: open source,
GitHub Action, won an independent 8-tool defect benchmark; alternatively a custom OpenCode review
pass as a CI step). Adopt risk tiering and demote review depth per tier based on evidence: delete
the tiers that have not caught anything in a month, rather than deciding to trust up front.

## Rung 5: containers (later, maybe never)

Worktrees plus per-session working directories cover single-workstation isolation. Containerize only
for full-autonomy permission settings without home directory exposure, or when work outgrows one
box. No mature open-source k8s operator for the full ticket-to-merge cycle exists (mid-2026); the
practical stack would be Argo Workflows + Jobs running `opencode run` with an API key Secret.
`kubernetes-sigs/agent-sandbox` is the primitive to watch. Everything from rungs 2-3 ports directly.

## Log

- 2026-06-10: plan created. Rung 1 scoped; recyclarr chosen as testbed.
- 2026-06-10: rung 1 expanded: CodeRabbit on recyclarr (free for public repos; verified against
  pricing pages, best OSS terms vs Greptile/Qodo/Graphite/BugBot) and a `pr-feedback` command as the
  human-triggered feedback loop (rung 3's loop with the human as poller).
- 2026-06-10: rung 1 artifacts built (`ticket`, `pr-feedback`, `dispatch`/`dispatch-done`,
  `notify.ts`). Audit fixes: tmux window keeps a shell after `opencode run` exits (preserves
  transcript and session resume), PRs created non-draft (CodeRabbit skips drafts), diff cap measured
  via `--shortstat`. Known tradeoffs: `notify.ts` fires for interactive sessions too (filter by
  session later if noisy); `gh pr create` will trigger a permission ask in headless runs, surfaced
  by the urgent notification, approve it in the ticket's tmux window or allow it in config once
  trusted.
- 2026-06-11: ticket command no longer hardcodes Linear state names ("In Review" doesn't exist on
  every team). It queries the team's workflow states once, maps an ACTIVE and an optional REVIEW
  state by type and name, and skips the review transition when no review state exists.
- 2026-06-11: first dispatch run failed on permission asks: headless `opencode run` auto-rejects
  them, it does not stall. The "approve in the tmux window" assumption from 2026-06-10 was wrong,
  and `notify.ts`'s urgent `permission.asked` notification is moot for dispatched sessions. Fix: new
  hidden primary agent `dispatch` (`exact_agents/dispatch.md.tmpl`), wired via `agent: dispatch` in
  the `ticket` and `pr-feedback` commands. Zero-ask permission surface: every global "ask" pattern
  resolved to allow (worktree-local git/file ops, `git push`, `gh pr create`) or deny (sudo, repo
  mutations, merges). File tools confined to the worktree via `external_directory: deny`; bash is
  the remaining escape hatch, accepted at this rung since PR review covers every output. OS-level
  sandboxing (bubblewrap around `opencode run`) is the upgrade path if that stops feeling
  comfortable.
- 2026-06-10: optional base branch arg: `dispatch <ID> [BASE]` bases the worktree on `origin/BASE`
  and the ticket command diffs against and targets it (`gh pr create --base`). Default remains
  origin's default branch. Motivation: long-lived topic branches (recyclarr `http-server`). Caveat:
  tickets stacked on a moving topic branch may need rebases; serialize them when possible.
- 2026-06-11: notify.ts was too noisy in practice: it fired for interactive TUI sessions and once
  per subagent idle. Reworked: notifications only when `OPENCODE_DISPATCH=1` (set via `tmux
  new-window -e` in `dispatch`, so the env survives into the post-run shell for `pr-feedback`
  reruns), subagent sessions filtered by `parentID`, and the `permission.asked` notification dropped
  entirely (moot for dispatch since the zero-ask agent; interactive sessions have the user at the
  keyboard).
- 2026-06-11: rung 1 testing surfaced a gap: a failed CI run with no review comments had no handler
  (`pr-feedback` read only comments and stopped). Extended `pr-feedback` to check `gh pr checks`,
  pull failing logs via `gh run view --log-failed`, and triage: fix failures the PR caused, rerun
  flaky or infra failures once, comment on the PR when a failure isn't addressable from the branch.
  This is rung 3's CI loop with the human as the poller, same as the comment loop.
- 2026-06-11: ticket command gained a sweep step before the diff gate: repo-wide `rg` for every
  symbol, config key, flag, or string the change touched, plus the old terminology on behavior
  changes. Agents kept updating only the files they edited and missing call sites and stale docs.
