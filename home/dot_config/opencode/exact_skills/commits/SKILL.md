---
name: commits
description: >-
  Use when explicitly authorized to commit, amend, fixup, or squash: staging, writing the commit
  message, handling commit-msg or pre-commit hook rejections, and rewriting earlier commits.
---

# Commits

## Procedure

- Run `git status --short`, `git diff -- <paths>`, and `git diff --cached` in one shell invocation;
  read intended untracked files directly. Do not inspect history or repeat evidence unless
  repository convention, state changes, or failure creates uncertainty.
- Use `git commit` with one `-m` each for the subject, every paragraph, every bullet, and the issue
  references. Each bullet value MUST start with `- ` (`-m "- Add X"`); without it, the bullet
  becomes a paragraph. Write unwrapped text; a global commit-msg hook joins bullets into one tight
  list, reflows, and validates. Never embed `\n` escapes in an argument.
- MUST NOT pass `--no-verify`. When the commit-msg hook rejects a message, edit the file it names
  without reading it first (it holds your message, subject verbatim, body reflowed), then rerun the
  same command with `-F <file>` in place of `-m`. When a pre-commit hook changes files, review the
  changes, re-stage them, and rerun.
- Join `git commit` and explicitly requested dependent operations with `&&` in one invocation (e.g.,
  `&& git push && chezmoi apply -- <target>`). Skip verification calls when output and exit status
  establish the result.
- Index rules (also for amend, fixup, and squash content): if the index already holds the exact
  intended commit, commit without paths or `-a`; if a nonempty index does not match, stop. Stage
  with `git add -A -- <paths>` or use `-a` only from an empty index.
- Stage the smallest safe path set. Collapse files to a directory only when every change below it
  belongs; file and directory paths may be mixed.
- To change an earlier commit, use `git commit --fixup=amend:<commit>` (message from
  `GIT_EDITOR="cp <file>"`; first line `amend! <subject>`, then the new message), or `--fixup` for
  content only, then `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <commit>~1`.

## Message layers

In order:

1. Subject (required): the durable outcome.
2. Context paragraphs: what prompted the change and why this approach, from relevant conversation
   context, not just the diff. Keep the concrete problem and its consequences, plus constraints or
   rejected alternatives behind surprising decisions. State reasons directly without recounting the
   conversation; explain what failed or was needed before the resulting rule (a principle alone is
   not a rationale). Omit only when subject and bullets leave nothing useful unexplained.
3. Bullets (optional): technical outline of distinct outcomes, boundaries, or notable details; may
   follow the subject directly when no context is needed.
4. Issue references (final `-m`): only for a tracker issue the task, branch, or plan names; never
   guess. `Fixes <ref>` when resolved, otherwise `Refs <ref>`.

- Each layer MUST add different information: bullets must not repeat subject or paragraphs, and
  paragraphs must not be unmarked bullets. Omit a layer with no unique information; never pad.
- Every claim must match the reviewed diff or verified session evidence. Omit routine process
  details and inventories of facts obvious from the diff.
- Read as a maintainer without the conversation: if why the change was needed, or why a surprising
  choice was deliberate, depends on missing context, replace abstract shorthand with concrete cause
  and consequence.
- Follow repository commit rules and report the resulting short SHA and subject.
