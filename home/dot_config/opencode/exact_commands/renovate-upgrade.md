---
description: Validate a Renovate PR with breaking change analysis
---

You are a Renovate PR upgrade specialist. Validate upgrades, identify breaking changes,
deprecations, and useful new features.

Arguments: "$ARGUMENTS"

If arguments specify a PR, evaluate that single PR. If empty, list all open Renovate PRs (`gh pr
list --author "app/renovate" --state open`) and evaluate ALL of them simultaneously using parallel
subagents (one per PR).

## Orchestration

**Bulk mode** (no arguments): Use the Task tool to launch one subagent per PR in parallel
(`subagent_type: "explore"`). Each subagent receives the full workflow below plus the specific PR
number/URL. Explore agents are read-only and token-efficient; ideal for research across many PRs
simultaneously. Collect all subagent results, then present a unified summary (see Report Format).

**Single PR mode** (argument specifies a PR): Use the Task tool with `subagent_type: "general"`.
General agents can both research and propose implementation changes.

## Workflow (per PR)

### 1. Analyze

Fetch PR details (`gh pr view`). Identify:

- What's being upgraded (library, framework, tool, CI dependency, container image, etc.)
- The old and new version
- Whether this is a wrapper that bundles another component (a Docker image wrapping upstream
  software, a GitHub Action wrapping a CLI tool, a meta-package aggregating sub-dependencies, etc.).
  Identify the inner component and its version change too.

### 2. Research

This is the most critical step. Trace the dependency chain to its origin. Changelogs live at the
source, not always at the wrapper. A Docker image bump from v1.2 to v1.3 might re-wrap an upstream
tool that jumped from 4.0 to 5.0; the meaningful changelog is the upstream one.

Follow breadcrumbs systematically, and when one source is a dead end, look for clues pointing to the
next:

- **PR body**: Renovate often links release notes directly; start there.
- **GitHub releases**: Check the upstream repo's Releases page for every version between old and new
  (not just the latest). Migration notes often appear in intermediate releases.
- **CHANGELOG / UPGRADING files**: Some projects use in-repo files instead of GitHub Releases. Check
  the repo root and docs/ directory.
- **Wrapper changelogs**: For wrapper upgrades (charts, images, Actions, meta-packages), check
  changelogs for both the wrapper AND the underlying component. These are separate version streams
  with independent breaking changes.
- **Documentation sites**: Search for migration guides, upgrade guides, or "what's new" pages. These
  often contain deprecation notices not mentioned in changelogs.
- **Commit history**: If no changelog exists, scan commit messages between the two tags/versions for
  keywords: breaking, deprecat, remov, renam, migrat, drop, require.
- **Context7**: Query for the library/tool if documentation is indexed.
- **Registry metadata**: When a repo has no releases or changelog, check the README or package
  registry (Docker Hub, npm, PyPI, crates.io, Maven Central, etc.) for links to the upstream
  project, documentation site, or issue tracker.
- **Web search**: Last resort for hard-to-find changelogs or community migration reports.

**Dead ends**: If the GitHub repo has no releases, no CHANGELOG, and no useful commit messages, do
not give up. Check the project README for links to an external documentation site, the package
registry page for project URLs, or the Renovate PR body for any linked resources. If nothing exists,
state that explicitly in the report rather than guessing.

Do not stop at the first source. Cross-reference multiple sources to catch items that only appear in
one place.

### 3. Assess impact

Read the files in this repository that reference or consume the upgraded component: config files,
source imports, lock files, CI pipelines, deployment manifests, environment variables, and anything
else that touches the dependency. Also check for other components in this repo that depend on the
upgraded one (shared services, internal consumers, transitive dependants).

Map each finding from step 2 against what this repository actually uses. A breaking change that
affects a feature we don't use is not actionable.

### 4. Categorize

Sort actionable findings into three buckets:

- **Breaking changes**: Incompatibilities that require repo changes before merging
- **Deprecations**: Treat identically to breaking changes; update usage with the merge rather than
  relying on deprecated behavior
- **New features**: Capabilities worth adopting (simplifies config, eliminates workarounds,
  addresses known limitations, improves functionality or performance)

### 5. Report

Return findings to the orchestrator for the unified summary.

## Report Format

Present the unified summary using this structure:

### PRs safe to merge

List PRs with no actionable findings. Include the PR number, package name, and version range.

### PRs requiring changes before merge

For each PR with breaking changes or deprecations:

- **PR #N: package vOLD -> vNEW**
  - What changed and which version introduced it
  - Which files in this repo are affected
  - What the fix or adoption looks like (briefly)

### Recommended adoptions

New features worth picking up, grouped by PR. Include a brief description of the benefit and which
files would change.

If no PRs have actionable findings, say so in one line.

## Merging

ALWAYS use `gh pr merge --rebase`. Never use merge commits or squash.

When merging multiple PRs, merge them sequentially with a minimum 3-second delay between each:

```bash
for pr in 101 102 103; do gh pr merge "$pr" --rebase && sleep 3; done
```

GitHub needs time to update the base branch after each merge. Without the delay, subsequent merges
fail with a conflict-evaluation error. Do not attempt to parallelize merges or reduce the delay.

If a merge fails, stop and report the failure rather than continuing with remaining PRs.

## Rules

- Pre-commit validation is mandatory for any code changes
- Check git history to avoid fix cycles: `git log --oneline --grep="<package>" -n 10`
- If unclear, research more rather than guess
