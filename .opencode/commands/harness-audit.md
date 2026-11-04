---
description: Audit OpenCode sessions for friction caused by the harness config
---

Find workflow friction between the user and agents in real OpenCode sessions, trace each case to the
managed OpenCode config under `home/dot_config/opencode/`, and report findings for the user to
select. Fix nothing until the user selects findings.

Arguments: $ARGUMENTS

- A window (`3w`, `2026-10-01`) sets `--since`; default `3w`.
- Other text narrows the focus (an agent, skill, command, or behavior); search for it first.

## 1. Collect candidates

Use `opencode-sessions` (see `--help`); every search uses the window and `--roots` unless a step
says otherwise. Run independent searches in parallel. Collect:

- **User corrections:** `search --in user` for correction phrasing: "why did you", "why are you", "I
  said", "stop", "instead", "wrong", "don't", "again", "should have", "you didn't", "gap",
  "instructions", "AGENTS", "skill", "approve". Ignore expanded slash-command bodies, usually the
  first user message, which match these words without expressing friction.
- **Rubber-stamp stops:** user replies that are only "yes", "go", "do it", or "approved". Many in
  one session suggest agents stopping for steps the request already authorized.
- **Dismissed or deflected questions:** `tools --name question --output`; flag dismissals and
  free-text answers that question or object instead of choosing, then check what the agent did next.
- **Recurring tool errors:** `tools --status error` without `--roots` so subagents count; group by
  error. Permission denials, invalid tool names or arguments, and repeated failed fetches point at
  permissions, tool descriptions, or prompts.

## 2. Establish root causes

For each candidate, read enough of the session (`show --range`, `show --grep`, `tools`) to state
what the user needed, what the agent did, and why. Before blaming the harness, check that the user
had not authorized or asked for the behavior.

Classify each case:

- **Caused:** an instruction or permission produced the behavior.
- **Gap:** no instruction covered a recurring, consequential situation.
- **Ignored:** a rule exists and the agent skipped it; find what made skipping easy (vague trigger,
  unobservable result, wrong placement).
- **Not harness:** model error, external tool, project-repo instructions, or user ambiguity. Report
  project-repo cases with their repository path; drop the rest.

Locate the owning file and quote the current rule. Run `git log --since <session date> -- <file>`;
when a later commit already fixed the case, mark it fixed.

## 3. Report and stop

Number the open findings. For each: one line on the friction, the session ID and message number, the
cause, and the owning `path:line`. Then list fixed, project-repo, and dropped cases in one line
each. Stop for the user to choose which findings to fix.

## 4. Fix selected findings

Load `instruction-authoring` before editing. Fix the cause, not the session's symptom; prefer
permissions or tooling over prose when enforcement is deterministic. Verify per this repository's
AGENTS.md. Do not commit unless asked.
