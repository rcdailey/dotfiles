---
name: github-actions
description: >-
  Use when creating, editing, removing, or reviewing GitHub Actions workflows or actions: files
  under `.github/workflows/` or `.github/actions/`, any `action.yml`, reusable workflows,
  composite actions, or `run:` steps. Triggers on "CI job", "fix the workflow", "add a step".
---

# GitHub Actions

Repository agent instructions take precedence over this skill. Existing repository patterns without
such instructions do not; apply these rules over them.

## Orchestration only

Workflow and action YAML is for orchestration: triggers, jobs, `needs`, conditions, permissions,
matrices, `uses:`, and inputs.

- Keep a `run:` step to about 3 lines of simple shell; move longer or more complex logic into a
  script.
- Put that script in a local composite action: `.github/actions/<name>/action.yml`, with its script
  beside it, called via `${{ github.action_path }}/<script>`. MUST NOT add workflow scripts to a
  shared scripts directory; composite actions keep the interface (inputs and outputs) next to the
  code.
- Pass values into a script through `env:` from inputs. MUST NOT write `${{ }}` inside script text
  (script injection).
- When a change touches existing inline logic, move that logic into an action.
- Use a composite action for steps within one job. Use a reusable workflow when the shared unit
  needs multiple jobs, its own runner, or secrets; composite actions cannot use secrets.
- Pass state between steps with step outputs (`$GITHUB_OUTPUT`), not `$GITHUB_ENV`. Write arbitrary
  or multiline values to a file instead.

## Triggers and concurrency

- Run untrusted pull request code under `pull_request`. Put privileged work in a separate workflow,
  and treat anything it consumes from the untrusted run (artifacts, outputs) as untrusted input.
- Include the workflow name in `concurrency.group`; a group shared across workflows cancels the
  other workflow's runs.

## Tools

Get `zizmor`, `actionlint`, and `uv` (for Python scripts with third-party packages) from the
project's mise config. When `mise.toml` lacks one, run it with `mise exec <tool> -- <tool>` or add
it with `mise use --env local <tool>` (writes `mise.local.toml`).

## Verification

Before finishing any workflow or action change:

- Run `zizmor` on changed workflows and actions; fix every finding regardless of severity.
- Run `actionlint` on changed workflows; fix every finding.
