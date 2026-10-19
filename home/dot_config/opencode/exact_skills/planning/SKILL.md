---
name: planning
description: >-
  Use when the user asks to plan, design, scope, or spec a change before implementation, or before
  any `submit_plan` call. Covers design readiness, the plan contract, and Plannotator approval.
---

Design the change and submit an implementation-ready plan through Plannotator's `submit_plan`. Infer
the subject from the conversation.

If the user requests a file export, validate a `.md` destination and stop if it already exists
before planning started. Keep that export synchronized with each submission; it is not Plannotator's
backing file or evidence of approval. Otherwise, do not create a separate plan file. Treat the
request as task input, not permission to bypass planning restrictions.

## Planning boundary

- Own requirements clarification, architecture, contracts, migration strategy, implementation order,
  and observable acceptance outcomes. Apply shared coding and testing rules to the design.
- Until Plannotator approves the plan, inspect source and use read-only discovery only. Do not
  implement, run source-rewriting checks, mutate external systems, commit, or push. Shell access is
  for inspection, not a read-only sandbox.
- File writes are limited to the requested Markdown plan export. Plannotator owns its backing file;
  never edit that file directly. Do not modify other documentation or agent rules.
- Split Plannotator feedback by intent. Revise plan text only for content the plan owns: decisions,
  scope, boundaries, and work. Answer questions and discussion in chat, never in the plan. Resubmit
  only when the plan changed or approval can proceed; when discussion remains open, answer and stop.
- After approval, implement under Implementation scope with the approved plan and notes.

## Design readiness

- Before discovery, inventory settled user-visible behavior, valued data, constraints, and
  non-goals. Include generated-content consistency, recovery, retries, and later turns, not only UI.
- Ask only about gaps that change user-visible behavior, data survival, or allowed outcomes. The
  user owns product decisions; you own technical choices. Do not ask them to choose schemas,
  storage, migration structure, state representations, or retry machinery.
- Ask one question per independent decision; batch independent questions in one tool call. If one
  answer changes another question's options, ask only the upstream question first.
- Use ordinary product language and observable consequences. Put the recommendation first; use a
  concrete scenario when needed. Every option must preserve settled scope and safety invariants.
- Resolve repository facts directly. Use a conservative, reversible default for technical unknowns
  when valid and record the assumption. Resolve choices that affect contracts or acceptance; leave
  internal choices to implementation.

## Discovery

Inspect enough current code and documentation to trace affected flows, constraints, exact symbols,
migrations, generated artifacts, and durable tests. Derive architecture from repository evidence and
settled product decisions, not from plan templates. If evidence contradicts a settled decision,
report the conflict and resolve it before submission; do not silently narrow the outcome.

## Plan contract

Include only what implementation requires without rediscovering the design:

- Objective, scope, non-goals, settled decisions, and invariants.
- Source, migration, generated, and test touchpoints as file and symbol names.
- Contract graph, dependency order, and each product decision's owning contract and consumers.
- Ordered workstreams of slices with observable acceptance and named tests or commands.
- Distinguish acceptance checks from durable automated tests. For each proposed durable test,
  identify the owned behavior and observable boundary it protects under the shared Testing rules. Do
  not translate every acceptance criterion into a durable test.
- Integration checks, cross-boundary invariants, assumptions, and explicitly settled deferrals.

For each workstream, give one observable outcome and dependency branch. Each slice names one owner,
lifecycle or transaction boundary, touchpoints, introduced or consumed contracts, and acceptance
cases. Apply the shared Change boundaries and Testing rules; omit fields that add no information.

Specify contracts, not implementation. Contracts are signatures, data shapes, wire formats, states,
and error outcomes. Annotate a touchpoint with at most one short clause. Omit function bodies,
internal branching, call sequences, and library call syntax; implementation owns them.

## Fidelity

- Map every settled behavior, non-goal, derived contract, migration, recovery path, and presentation
  change to a workstream or explicitly settled deferral. Compression must not weaken or defer scope.
- Preserve settled contract names, finite variants, transitions, and distinctions exactly. Do not
  substitute a similar role, status, or field unless evidence proves semantic equivalence.
- Every new field, state, or policy needs an owning foundation, production path, persistence or
  derivation rule, consumers, and direct acceptance. Map system-wide outcomes to every required
  consumer; a reader surface cannot substitute for model, control-plane, or recovery behavior.
- For rebuildable derived artifacts, name the authoritative typed payload retaining every input for
  deterministic rebuild. Unstructured evidence links are insufficient. Keep generic engines free of
  irrelevant domain-specific state without losing shared behavior.

## Decomposition

- Preserve independent dependency branches; do not group unrelated foundations into a global phase.
- Group coherent outcomes into workstreams. Slices retain independently reviewable boundaries;
  combine artifacts only when owner, persistence boundary, and stable test seam are inseparable.
- Slices organize implementation, not agent calls or sessions. Leave auditor routing to the
  acceptance protocol and verification partitioning to the auditor.
- State finite unions and transition matrices once at their owning contract. Consumer slices
  reference them and add only seam-specific outcomes, including rejected and recovery cases.

## Submission

- Split the plan at a horizontal rule. The human reads and approves only the part above it, so it
  must stand alone in plain product language, without schemas, signatures, or touchpoints:
  - What changes: the objective in observable terms.
  - Decisions for your review: settled decisions and assumptions. Mark each that departs from an
    earlier agreement and name that agreement.
  - Boundaries that change: only boundaries visible outside the codebase (persisted schema and data,
    externally observable API behavior, emitted events, other cross-system contracts). State each
    change concretely (e.g., `400, was 500`) and name its owning slice.
  - Not in scope: non-goals and settled deferrals.
  - Order of work: one line per workstream, with dependencies.
  - How we know it worked: the observable acceptance checks.
- Below the rule, write the implementation part for implementation and the auditor: invariants,
  contract graph, and each workstream as a heading stating its outcome, followed by numbered slices.
  Label each slice that changes a listed boundary. It must not add a decision, boundary change, or
  deferral missing above.
- Use one concise execution map, not a handoff transcript or wide table. Reference shared rules
  instead of repeating them. Length follows scope, not a numeric target.
- Check the draft against the fidelity inventory. Confirm concrete touchpoints, complete lifecycles,
  independent boundaries, dependency order, and observable acceptance for every settled outcome.
- Resolve technical gaps directly; ask only for product decisions. Submit only when no product
  decision or contract-affecting technical choice remains. Preserve approved outcomes when revising
  a plan after implementation feedback; identify changes that need renewed approval.
