## Testing

- Keep durable tests for contracts: stable behavior a user, caller, or external system relies on,
  including tooling contracts, permissions, mutation safety, and recovery. Use temporary checks for
  one-off scaffolding and private details; remove temporary artifacts before handoff.
- Low-level tests that verify initial implementation are temporary; before commit, keep only those
  that protect a named contract.
- Before adding a durable test, name the contract the change adds or alters; with none, add no
  durable test. Otherwise write it first and confirm it fails for the expected reason when
  practical.
- Test through the stable observable boundary that owns the behavior. Broaden scope when the outcome
  spans components. Do not narrow scope merely to reach internal code.
- Assert observable output, state, or effects. Verify an interaction only when that interaction is
  the contract, and assert only contract-relevant details.
- When correctness depends on an external system's semantics, test against the real system or a
  supported emulator that preserves those semantics. Doubles may isolate callers, but MUST NOT stand
  in for that system when testing its adapter. If neither is available, report the gap instead of
  adding a durable test.
- Durable tests must survive behavior-preserving refactors. Change expected outcomes only when the
  contract changes. Do not test passive data plumbing or add tests merely to exercise private
  internals, branches, or lines. Do not expose implementation details or add production code solely
  for tests.
- Existing tests may reveal current behavior, but their design is not precedent. These principles
  MUST take precedence over local test patterns. When a change requires editing an existing test,
  name the contract it protects: rewrite it at the right boundary if one exists; otherwise delete
  it. Make the smallest behavior-preserving refactor needed to expose a stable boundary, and leave
  unrelated tests unchanged.
- For conditional or stateful behavior, cover each distinct observable outcome. Use representative
  inputs for equivalent cases, plus relevant boundary, initial, empty, allowed-transition, and
  rejected-transition cases.
- If no stable observable boundary exists, state why and use a temporary proof when useful rather
  than adding a coupled regression test.
- Write the full output of slow test or build runs to a file under the temp directory, then search
  that file. Rerun only when code, inputs, or environment changed, or to probe one named test for
  flakiness; never rerun to recover output a filter discarded.
