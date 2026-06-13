# Agent factory plan

Status: rung 1 in progress. Testbed: recyclarr.

A staged plan for moving from interactive TUI sessions to supervised, ticket-driven agent workflows
on a local workstation. Each rung removes one piece of manual involvement; the climb stops wherever
trust runs out. This file holds the plan and durable decisions; behavior details live in the
artifacts themselves, and history lives in git.

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
- Industry baseline (researched Jun 2026, primary sources): interactive use dominates; autonomous
  ticket-to-PR agents are a real but minority workflow (agent traces in ~16-23% of GitHub projects,
  a fraction of commits within those; arxiv.org/html/2601.18341v1). Hosted products (Copilot coding
  agent, Codex cloud, Jules) converged on ticket-as-trigger, PR-comments-as-iteration; Devin's
  persistent-session alternative shows the worst outcome data (54% of its unmerged PRs died of
  inactivity; arxiv.org/html/2602.00164v1), which validates the fresh-session/PR-as-memory choice.
  No credible practitioner endorses merge-on-AC without human review for production code; the
  spectrum runs from Willison's "explain every line"
  (simonwillison.net/2025/Mar/19/vibe-coding/) to Ronacher's harness-engineering stance, all on the
  review side. Defect data points the same way: AI-co-authored PRs carry ~1.7x more issues, and AI
  review tools top out near 50-60% F1 (Martian Code Review Bench), so they remain a first-pass
  filter, not a gate. Steering an agent mid-task degrades output (Cognition's own Devin guidance);
  front-load the spec, iterate after it finishes.
- Skill formation is a deliberate trade (Anthropic research, Feb 2026: AI assistance measurably
  hurts comprehension when learning new libraries). Hashimoto's framing applies here: delegate the
  slam dunks, keep working manually on whatever you want to stay sharp at
  (mitchellh.com/writing/my-ai-adoption-journey). This is the basis for the verdict-vs-question
  routing rule below.

## Workflow rules

- The unit of work picks the workflow, not the repo. Hand-driven TUI sessions keep committing to
  main (review happened synchronously). Dispatched tickets always go through a branch and PR (review
  happens asynchronously).
- Tickets exist only as dispatch fuel. No ticket regime for interactive work.
- Routing signal for dispatch vs interactive: can the review be given in verdicts? If feedback
  would mostly be questions (new library, unformed taste), the learning is the work; do it
  interactively, or dispatch a first draft and pull it into a TUI session in the worktree. PR
  comments carry verdicts well and dialogue poorly (evidence: recyclarr PR 859 / REC-151).
- Solo repos: no branch protection or required approvals. The PR is an inspection surface, not a
  gate; merge stays one keystroke after a green skim.

## Rung 1: supervisor ergonomics (current)

You trigger everything, you review everything. The deliverable is calibration, not automation: after
~10 tickets, know the agents' failure patterns, the ticket-writing quality bar, and whether PRs
deserve a lighter touch.

Artifacts (all in this repo; each file is the authoritative spec of its own behavior):

1. `home/dot_config/opencode/exact_commands/ticket.md`: the dispatch prompt template (Linear
   lifecycle, test-first implementation, repo-wide sweep, diff cap, PR creation). This template is
   where supervision lives; iterate on it after every dispatched ticket.
2. `home/dot_config/exact_zsh/functions/`: `dispatch <ID> [BASE]` (worktree + tmux window + headless
   run), `dispatch-feedback <ID> [PR]` (trigger a feedback iteration), `dispatch-done <ID>`
   (teardown).
3. `home/dot_config/opencode/exact_plugins/notify.ts`: `notify-send` on idle, dispatched top-level
   sessions only.
4. `home/dot_config/opencode/exact_commands/pr-feedback.md`: feedback iteration; triages and
   addresses failing CI checks and review comments, replies to every comment.
5. CodeRabbit GitHub App on recyclarr (full Pro tier is free for public repos). Supplements, not
   replaces, the human pass at this rung. Tune `.coderabbit.yaml` until the signal is worth reading.

Daily flow: write/refine tickets in Linear (`to-issues`), `dispatch ENG-123`, keep doing interactive
work, get notified, wait for CI + CodeRabbit, review the PR line-by-line as today. Feedback goes on
the PR as review comments, then `dispatch-feedback ENG-123` (also the trigger for red CI runs).
Trivia gets fixed by hand. Merge, `dispatch-done`, then record what the ticket template should have
said to prevent whatever went wrong.

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
view`). On failure or feedback it runs `pr-feedback` in a fresh session against the PR; the PR body
and reply threads carry the context (no session state to persist across dispatcher restarts).
Tickets land in "Ready for human review" only when checks pass.

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

## Decisions

Durable rationale that the artifacts cannot explain on their own. Chronology lives in git history.

- Headless `opencode run` auto-rejects permission asks; it does not stall waiting for approval.
  Hence the hidden `dispatch` primary agent (`exact_agents/dispatch.md.tmpl`) with a zero-ask
  permission surface: worktree-local ops, `git push`, and `gh pr create` allowed; sudo, repo
  mutations, and merges denied; file tools confined to the worktree. Bash remains the escape hatch,
  acceptable while every output goes through PR review; OS-level sandboxing (bubblewrap) is the
  upgrade path if that stops feeling comfortable.
- PR-as-memory: every feedback iteration runs in a fresh session. The dispatcher at rung 2+ can
  restart, so fresh sessions must work regardless; session reuse would only add sunk-cost bias
  toward defending the original code plus context-window degradation. The ticket command writes
  design notes into the PR body (constraints, rejected alternatives, dead ends; what a fresh session
  cannot infer from the diff), and reply threads record per-comment decisions across iterations. The
  design-notes body intentionally overrides the global "keep PR descriptions high-level" directive.
- Every comment gets a reply, bots included: review bots like CodeRabbit learn from responses. Bot
  replies are neutral, factual, and conclusive; human threads can keep arguing. GitHub code scanning
  findings arrive as ordinary review threads (`github-advanced-security[bot]`, verified on recyclarr
  PR 859), so the comment loop covers them without extra tooling.
- CodeRabbit picked over Greptile/Qodo/Graphite/BugBot: best terms for public OSS repos (full Pro
  free).
- Stacked tickets on a moving topic branch (`dispatch <ID> <BASE>`) may need rebases; serialize them
  when possible.
