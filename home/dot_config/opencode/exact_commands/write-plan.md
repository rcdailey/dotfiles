---
description: Write a delegation-ready plan from the current design
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
Produces: <artifact or durable state made available>
Depends on: <accepted earlier slices or existing contracts>
Excludes: <adjacent behavior reserved for later slices>
Acceptance:
- <observable case through the direct stable seam>
```

## Decomposition

Inventory each behavior's owner, production boundary, produced artifact, consumer, and stable test
seam. Behaviors may share a slice only when those facts match.

Split distinct:

- Transactions or lifecycle entry points
- Contract definition, production, consumption, and presentation
- Schema ownership from runtime consumers
- Backend behavior from frontend state and presentation
- Acceptance requiring fixtures from different subsystems
- Dirty-work isolation from semantic implementation

Each slice must be independently reviewable, revertible, and committable. It owns its direct durable
tests; do not create a later catch-all testing slice. Shared feature names or invariants do not
justify combining boundaries.

## Audit

Before writing, verify:

1. Every slice has one owner, boundary, artifact, and stable acceptance seam.
2. Every acceptance case maps to exactly one slice.
3. Dependencies are explicit and no slice consumes an undefined contract.
4. Exclusions prevent later behavior from leaking into earlier slices.
5. No slice combines recovery, cleanup, or presentation with an independent production boundary.

Resolve audit failures by splitting the plan. If splitting exposes an unsettled architectural
decision, ask one bounded question and stop until answered.

Write the plan, then report its path and any intentionally deferred decisions. Do not delegate
implementation, modify production code, commit, or push.
