## Testing

SHOULD write a failing test before implementing features and fixes (test-first). Test at the highest
scope that's practical; push to lower-scoped tests only when higher-scoped tests cannot reach
specific code paths.

Add durable tests when behavior changes and a stable observable boundary exists. The primary owns
acceptance cases; implementing agents write the smallest proof of those cases. Show that each new
test fails for the expected reason before changing production code when practical. If no stable seam
exists, state why instead of adding an implementation-coupled test.

**Assert outcomes, not interactions.** Verify the result, side effect, or state change rather than
asserting a mock method was called. Interaction verification couples tests to implementation; they
break on refactors even when behavior is correct. If interaction verification feels like the only
option, challenge the design first. Skip anything with no meaningful behavior to verify. Avoid
over-mocking, duplicate coverage, test-only production code, and magic constants.

A behavior-preserving refactor should not require expected-value changes. Update expectations only
when the contract changes. Do not add tests merely to cover private helpers, branches, or lines.

For predicates and lifecycle boundaries, test both sides of each boundary. Include the empty or
first state when later states have different prerequisites; one production example is not a matrix.

Run the smallest relevant tests while implementing. Before handoff, run the repository's declared
completion check once; do not repeat broad checks after intermediate edits. Run broad repository
checks again at the integration boundary unless repository instructions require another cadence.

**Debugging test failures:** Gather evidence before changing code. Avoid guess-and-check cycles.

1. Read assertion output carefully; diff output often reveals the issue immediately.
2. Add temporary logs or intermediate assertions to locate the divergence; remove them when done.
3. Compare with passing cases, reduce to a minimal reproduction, and check isolation.
