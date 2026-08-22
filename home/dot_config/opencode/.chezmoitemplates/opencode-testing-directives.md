## Testing

SHOULD write a failing test before implementing features and fixes (test-first). Test at the highest
scope that's practical; push to lower-scoped tests only when higher-scoped tests cannot reach
specific code paths.

Add permanent durable tests only for repository product code and modularized Python CLI projects
governed by `python-scripting`. For supporting code and standalone scripts that are not the product,
use ad hoc behavior checks or temporary tests, and delete temporary test artifacts before handoff.
In either case, write the smallest proof and show it fails for the expected reason before changing
production code when practical. If no stable seam exists, state why instead of adding an
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
