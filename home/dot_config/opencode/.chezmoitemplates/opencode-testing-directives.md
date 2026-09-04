## Testing

- Keep durable tests only for product behavior. Verify support code with ad hoc or temporary checks,
  and remove temporary artifacts before handoff.
- For a feature or fix, write a behavioral test first and confirm it fails for the expected reason
  when practical.
- Test through the stable observable boundary that owns the behavior. Broaden scope when the outcome
  spans components. Do not narrow scope merely to reach internal code.
- Assert observable output, state, or effects. Verify an interaction only when that interaction is
  the contract, and assert only contract-relevant details.
- Durable tests must survive behavior-preserving refactors. Change expected outcomes only when the
  contract changes. Do not test passive data plumbing or add tests merely to exercise private
  internals, branches, or lines. Do not expose implementation details or add production code solely
  for tests.
- Existing tests may reveal current behavior, but their design is not precedent. These principles
  MUST take precedence over local test patterns. For tests added or changed, reuse a pattern only
  when it complies; otherwise replace it. Make the smallest behavior-preserving refactor needed to
  expose a stable boundary, and leave unrelated tests unchanged.
- For conditional or stateful behavior, cover each distinct observable outcome. Use representative
  inputs for equivalent cases, plus relevant boundary, initial, empty, allowed-transition, and
  rejected-transition cases.
- If no stable observable boundary exists, state why and use a temporary proof when useful rather
  than adding a coupled regression test.
- Run targeted tests while editing and the repository completion check after the final change.

When a test fails, inspect the evidence and isolate the cause before changing code. Remove temporary
diagnostics.
