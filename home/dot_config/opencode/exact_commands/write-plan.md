---
description: Write an implementation-ready plan from the current design
agent: build
subtask: false
---

Write a new implementation plan from the settled decisions in this conversation and repository
evidence. Do not implement the plan.

Arguments: $ARGUMENTS

## Target

- If arguments include a path, validate it as the destination.
- If arguments describe the plan without a path, follow the repository's plan location and naming
  convention.
- If arguments are empty, infer the subject and destination from the current conversation.
- If the destination already exists, stop and report it. This command creates new plans; it does not
  refactor existing ones.
- Ask only when a missing decision would change architecture, a public contract, an invariant, or
  acceptance. Resolve minor omissions from repository evidence.

## Plan

Capture only information needed to implement and verify the settled design:

- Objective, current state, scope, and non-goals
- Architectural decisions, ownership, invariants, and dependency order
- Ordered implementation slices with direct durable acceptance
- Phase-level acceptance, verification cadence, and completion protocol

For each slice, specify:

```txt
Outcome: <one observable result>
Owner: <one component that owns the state or contract>
Boundary: <one transaction, endpoint, worker, contract, or UI transition>
Introduces: <new reusable contract or artifact, or n/a>
Consumes: <existing or earlier accepted contracts and artifacts, or n/a>
Excludes: <adjacent behavior reserved for later slices>
States: <every reachable variant and legal or stale transition, or n/a>
Acceptance:
- <observable case through the direct stable seam>
```

## Decomposition

Build the contract graph before behavior slices. Every new reusable schema, API, event, repository
contract, or persisted artifact gets a foundation slice with direct contract acceptance. A later
slice may consume it only after that foundation is accepted. No slice may introduce and behaviorally
consume the same reusable contract.

Then inventory each behavior's owner, boundary, consumed contracts, state matrix, and stable test
seam. Behaviors may share a slice only when those facts match.

Split distinct:

- Transactions or lifecycle entry points
- Contract definition, production, and behavioral consumption
- Pure state reduction, request or action orchestration, durable hydration or recovery, and
  presentation
- Schema ownership from runtime consumers
- Backend behavior from frontend state and presentation
- Acceptance requiring fixtures from different subsystems
- Dirty-work isolation from semantic implementation

Each slice must be independently reviewable, revertible, and committable. It owns its direct durable
tests; do not create a later catch-all testing slice. Shared feature names or invariants do not
justify combining boundaries.

Slices are acceptance units, not agent calls. The primary implements them directly; do not prescribe
an agent or session per slice. A contract slice may include generated output or nonbehavioral
exhaustiveness scaffolding needed to keep compilation green, but not behavioral consumption.

For a finite response union or state machine, enumerate every reachable variant, legal transition,
stale transition, and observable route. "Use the existing contract" is not an acceptance matrix.

## Audit

Before writing, verify:

1. Every reusable contract has one foundation slice with direct contract acceptance.
2. No slice introduces and behaviorally consumes the same reusable contract.
3. Every consumed contract already exists or comes from an earlier accepted slice.
4. Every behavior slice has one owner, boundary, state matrix, and stable acceptance seam.
5. Every acceptance case maps to exactly one slice.
6. Exclusions prevent later behavior from leaking into earlier slices.
7. No slice combines recovery, cleanup, or presentation with an independent production boundary.

Resolve audit failures by splitting the plan. If splitting exposes an unsettled architectural
decision, ask one bounded question and stop until answered.

Write the plan, then report its path and any intentionally deferred decisions. Do not delegate
implementation, modify production code, commit, or push.
