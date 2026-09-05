---
description: Write a concise implementation plan from the current design
agent: build
subtask: false
---

Write one concise implementation plan from settled decisions and repository evidence. The primary
will implement it directly and delegate independent acceptance. Do not implement the plan.

Arguments: $ARGUMENTS

## Target

- If arguments include a path, validate it as the destination.
- If arguments describe the plan without a path, follow the repository's plan location and naming
  convention.
- If arguments are empty, infer the subject and destination from the current conversation.
- If the destination already exists, stop and report it. This command creates new plans; it does not
  refactor existing ones.

## Design readiness

Before repository discovery, inventory the settled user-visible behavior, valued data, constraints,
and non-goals from the conversation and cited documents. Identify only gaps whose answers would
change what the user experiences, what data survives, or which outcomes are allowed.

User-visible behavior includes generated-content consistency, recovery, retries, and later turns,
not only UI. Translate technical gaps into product consequences without narrowing the original
outcome or treating one story-specific example as the feature's full scope.

Treat the user as the product owner, not the code architect. Ask about desired behavior and data
consequences. Do not ask the user to choose contract shapes, state representations, schemas, storage
strategies, migration structure, retry machinery, event vocabularies, or other implementation
details. The primary owns those decisions and chooses the simplest option consistent with settled
behavior, repository constraints, and data safety.

Ask one separate question per independent product decision. Put independent questions in one
question-tool call. If one answer changes another question's options, ask only the upstream question
and stop. Every option must preserve settled scope and vary only the missing decision.

Write questions in ordinary product language. Define unavoidable terms inline. Each option must say
what the user will observe and include a concrete scenario when the effect is not obvious. Put the
recommendation first and explain why it fits the stated goals. Do not expose internal identifiers or
ask for facts the repository can establish. When an unknown technical fact has a conservative,
reversible default, use it and record the assumption.

Before offering options, reject any that violate settled behavior or active authority, data-safety,
atomicity, stale-result, and fail-closed invariants. A recommendation must satisfy all of them.

For example, ask what should happen when a checker cannot evaluate good prose. Do not ask the user
to choose a retry topology.

## Discovery

After design readiness passes, inspect only enough current code and documentation to locate exact
touchpoints, symbols, migrations, generated artifacts, and durable tests. Do not run broad discovery
to redesign product behavior. Derive the technical design from current repository constraints and
the settled product decisions. Do not inspect history solely to learn plan style.

## Content

Include only what the primary needs to implement without rediscovering the design:

- Objective, scope, non-goals, settled decisions, and invariants
- Exact source, migration, generated, and test touchpoints with relevant symbols
- A compact contract graph and dependency order
- Traceability from each product decision to its owning contract, producer, and consumers
- Ordered workstreams with durable acceptance checkpoints
- Integration checks, cross-boundary invariants, and deferred decisions

For each workstream, give one observable outcome and one dependency branch. For each checkpoint,
name one owning component, one lifecycle or transaction boundary, exact touchpoints, contracts
introduced or consumed, and acceptance cases with named tests or commands. Omit fields that add no
information.

## Fidelity

Before drafting, inventory every settled behavior and non-goal plus every derived contract,
migration, recovery path, and presentation change. Map each one to one workstream or to an
explicitly settled deferral.

Compression must not replace, weaken, merge, or defer settled behavior. Repository evidence may
resolve implementation details, but it may not silently change the design. If evidence contradicts a
settled decision, report the conflict and stop instead of choosing a different design.

Preserve settled contract names, finite variants, transitions, and distinctions exactly. Do not
rename, collapse, or reinterpret one state as another to simplify the plan.

Represent every distinct product rule directly in the technical design. Do not use an existing role,
status, or field as a proxy unless repository evidence proves it has the same meaning. Every new
field, state, or policy referenced by behavior needs an owning foundation, production path,
persistence or derivation rule, consumers, and direct acceptance.

Map system-wide outcomes to every required consumer. A reader surface does not replace model,
control-plane, recovery, or persistence behavior needed to keep later generated content consistent.

For a rebuildable derived artifact, name the authoritative typed payload that retains every input
needed for deterministic rebuild. An evidence link to unstructured text is not sufficient. Features
in a generic engine must omit irrelevant story-specific state without losing shared behavior.

## Decomposition

Honor the active direct-implementation and acceptance constraints. Preserve independent branches in
the contract graph. Do not block one branch on an unrelated foundation or organize all foundations
into a global first phase.

Use workstreams to group a coherent outcome along one dependency branch. A workstream may cross
components, but its checkpoints retain their real implementation and acceptance boundaries. Do not
split a coherent branch merely to make every checkpoint a top-level section.

Use compact ordered checkpoints that honor the active contract, producer, consumer, and recovery
slice boundaries. Combine artifacts only when they share an owner, persistence boundary, and stable
test seam and cannot be accepted separately.

Checkpoints organize implementation, not agent calls, sessions, or commits. Name observable acceptance
cases and cross-boundary invariants; the active acceptance protocol owns auditor task routing and
partitioning.

State a finite union or state matrix once at its owning contract. Consumer steps reference it and
add only behavior specific to their seam. Do not repeat stale-result, idempotence, serialization, or
fail-closed requirements unless the observable behavior differs at that boundary.

## Brevity

This is an execution map, not a handoff transcript. Use short checkpoint subsections and bullets; do
not put detailed checkpoint content in wide Markdown tables. Do not repeat repository guidance,
settled design prose, state matrices, acceptance cases, or the active acceptance protocol. Keep one
document even when the graph has parallel branches. Plan length follows scope; do not use a numeric
line target as an acceptance criterion.

Finish the content and satisfy active authoring limits before creating the file. After creation, do
not delete and recreate it or rewrite it wholesale for brevity or wrapping. Make only surgical
corrections required for accuracy or validation.

## Final check

Compare the draft with the fidelity inventory. Confirm that every item is present unchanged, every
foundation precedes separate producer and consumer checkpoints, and every checkpoint names one real
owner, entry point, and stable acceptance seam. Confirm that recovery is separate when its entry
point differs and acceptance covers cross-component boundaries. Confirm touchpoints are concrete,
parallel work remains parallel, and no section repeats another. Reject conditional implementation
choices, inferred backfill semantics, and checkpoints with multiple entry points. Confirm every product
distinction has a direct contract representation and every new field has a complete lifecycle.
Confirm presentation does not substitute for required system
consumers. Resolve technical gaps directly; ask only when the answer changes user-visible behavior
or valued data. Restore omissions and split invalid checkpoints before writing.

Claim the plan is ready to implement only when no product decision or technical gap remains
unresolved. Write the plan, then report its path and deferred decisions. Do not delegate
implementation, modify production code, commit, or push.
