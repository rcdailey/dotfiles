---
name: commit
description: >-
  Use when the user explicitly authorizes creating, amending, fixing up, or squashing a commit.
  Covers the `commit save` workflow and commit message composition. Do not use to decide whether a
  commit is authorized.
---

# Commit

`git commit` is denied; `commit save` is the only commit path.

## Workflow

- Run `git status --short`, `git diff -- <paths>`, and `git diff --cached` in one shell invocation.
  Read intended untracked files directly. Do not run `commit save --help`, inspect history, or
  repeat evidence unless repository convention, state changes, or failure creates uncertainty.
- Use `commit save <paths> -s "<subject>"`, with repeated `-p` paragraphs and `-b` bullets when
  needed. Never embed `\n` escapes in an argument.
- `commit save` also amends the tip commit and creates fixup or squash commits for an earlier
  commit. When amending, passing `-s` replaces the whole message, so re-supply every `-p` and `-b`
  that should survive.
- After a failed `commit save`, fix it with `commit retry` passing only the corrected options; each
  given option replaces that whole layer, the rest is reused.
- Run `commit save` and explicitly requested dependent operations in one shell invocation, joined by
  `&&`. For example, append `&& git push && chezmoi apply -- <target>`. Do not add verification
  calls when command output and exit status establish the result.
- If the index already contains the exact intended commit, omit paths and `-a`. If a nonempty index
  does not match, stop; path and `-a` modes are only for an empty index. Amend, fixup, and squash
  follow the same rule for their content.
- Pass the smallest safe path set. Collapse files to a directory only when every change below it
  belongs in the commit; file and directory paths may be mixed.
- Follow repository commit rules and report the resulting short SHA and subject.

## Message

Compose in semantic order:

1. The required subject states the durable outcome.
2. Context paragraphs explain what prompted the change and why this approach was chosen. Use
   relevant conversation context, not just the final diff. Preserve the concrete problem and its
   consequences, plus constraints or rejected alternatives that explain otherwise surprising
   decisions. State the reasons directly, without recounting the conversation. Explain what failed
   or was needed before stating the resulting rule; a design principle alone is not a rationale.
   Omit these paragraphs only when the subject and bullets leave no useful context unexplained.
3. Optional bullets provide a technical outline of distinct implementation outcomes, boundaries, or
   notable details. They may follow the subject directly when no contextual explanation is needed.
4. Issue references (`-i`) link the commit to a tracker issue the task, branch, or plan names; never
   guess. Use `Fixes <ref>` when the commit resolves it, otherwise `Refs <ref>`.

- Every layer MUST contribute different information. Bullets must not repeat the subject or
  paragraphs, and paragraphs must not be bullets with their markers removed. Omit an optional layer
  only when it has no unique information; do not invent content to complete the structure.
- Every claim must match the reviewed diff or verified session evidence. Omit routine process
  details and exhaustive inventories of facts already obvious from the diff.
- Read the message as a maintainer without the conversation. Can they understand why the change was
  needed and why any surprising choice was deliberate? Replace abstract shorthand with the concrete
  cause and consequence when either answer depends on missing context.
