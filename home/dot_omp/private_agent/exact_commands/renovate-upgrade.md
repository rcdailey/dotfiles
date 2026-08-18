---
description: Analyze one or all open Renovate upgrades in parallel
---

Analyze Renovate upgrade pull requests with the `upgrade-analyst` agent.

Arguments: $ARGUMENTS

If arguments identify one PR, analyze only that PR. Otherwise use the `github` tool to find every
open PR authored by Renovate in the current repository. Return immediately when none exist.

Dispatch one `upgrade-analyst` task per PR in one parallel `task` call. Give each task only the
repository identity and PR number; the agent owns research and output. Cross-check any finding that
controls merge safety against its cited source or repository path.

Aggregate results under:

1. `Safe to merge`
2. `Requires changes`
3. `Recommended adoptions`

For each PR include its number, package, version range, CI status, and merge-safety verdict. Do not
merge until the report is presented and the user explicitly approves specific PRs.

After approval, merge sequentially with rebase and wait at least three seconds between PRs. Stop on
the first failure.
