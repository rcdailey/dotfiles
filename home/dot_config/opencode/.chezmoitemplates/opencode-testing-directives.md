## Testing

SHOULD write a failing test before implementing features and fixes (test-first). Test at the highest
scope that's practical; push to lower-scoped tests only when higher-scoped tests cannot reach
specific code paths.

**Assert outcomes, not interactions.** Verify the result, side effect, or state change rather than
asserting a mock method was called. Interaction verification couples tests to implementation; they
break on refactors even when behavior is correct. If interaction verification feels like the only
option, challenge the design first. Skip anything with no meaningful behavior to verify. Avoid
over-mocking, duplicate coverage, test-only production code, and magic constants.

**Debugging test failures:** Gather evidence before changing code. Avoid guess-and-check cycles.

1. Read assertion output carefully; diff output often reveals the issue immediately.
2. Add temporary logs or intermediate assertions to locate the divergence; remove them when done.
3. Compare with passing cases, reduce to a minimal reproduction, and check isolation.
