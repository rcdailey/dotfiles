# Agent Development Framework

- Status: Working draft
- Date: 2026-08-15
- Scope: Personal and workplace software development across repositories
- Research: [Agent Development Framework Research](agent-development-framework-research.md)

## Purpose

Coding agents can produce plans, issues, code, and tests faster than a person can understand and
review them. The framework exists to keep human comprehension and judgment in control without
giving up the useful speed of agents.

The framework is repo-agnostic. Its interaction layer runs locally through OpenCode and applies to
personal and workplace repositories. Repository-specific rules remain in each repository.

## North star

An agent may accelerate exploration and execution, but a human owns intent, architecture, risk,
and acceptance. The framework keeps work small enough to understand, records consequential
decisions, and prevents progress when required decisions or evidence are missing.

The intended experience is a conversation, not an approval queue. At each consequential point, the
human can ask questions, challenge assumptions, request examples, revise the proposal, or reduce
the scope before deciding whether work may continue.

## Design principles

### Protect comprehension

Comprehension is a constrained resource. The framework presents one decision at a time, uses
progressive disclosure, and limits the size of plans and implementation slices. When an artifact
cannot be reviewed without skimming, the artifact or work unit is too large.

### Keep human decisions interactive

The framework preserves the design discussion that occurs before implementation. It must not
silently convert that discussion into approved issues or executable work. Generated intent,
decisions, and decomposition remain proposals until the human discusses and approves them.

### Externalize state

Workflow state must not live only in conversation history, model context, or prose plans. It must
be durable, queryable, and associated with the exact work it governs.

### Match controls to observed failures

Use the lightest control that addresses a demonstrated problem. For interactive work with a
compliant model, agents, skills, and commands may provide enough structure. Add deterministic
controls only when unattended execution, repeated scope violations, multiple writers, destructive
actions, or workplace policy create a concrete need.

### Work in bounded slices

Only one independently reviewable slice should be active at a time. Each slice has one principal
purpose, explicit acceptance claims, and evidence that can be evaluated without reconstructing the
entire feature.

### Prefer evidence over claims

An agent saying that work is complete is not evidence. Tests, builds, static checks, demonstrations,
runtime observations, and independent review provide evidence. Evidence is bound to the exact
revision it evaluated and becomes stale when that revision changes.

### Separate production from verification

The implementing agent is not the only judge of its work. Verification should use fresh context,
independent tools or agents, and human judgment where risk warrants it.

### Adapt rigor to risk

Trivial changes should not require architectural ceremony. Cross-cutting, persistent, destructive,
security-sensitive, or difficult-to-reverse changes require deeper intent, review, and evidence.
The framework selects the required controls from explicit risk, scope, and uncertainty.

### Remain portable

The framework must not depend on one repository, issue tracker, employer, model, or hosted service.
Integrations are adapters around a local core. Repository policy may strengthen the framework but
must not redefine its basic lifecycle.

### Evolve from use

Start with the smallest useful control loop. Add a mechanism only after real use exposes a specific
failure that the mechanism prevents. This document guides those changes and prevents the framework
from growing into an unrelated orchestration platform.

## Intended lifecycle

The eventual lifecycle is an explicit state machine:

```text
Exploring
-> Intent Review
-> Intent Approved
-> Decomposition Review
-> Slice Ready
-> Implementing
-> Evidence Ready
-> Independently Verified
-> Human Accepted
-> Mergeable
```

Transitions are framework operations, not labels that an agent changes on its own. The framework
may omit states for low-risk work, but it must do so through policy rather than agent discretion.

## Core artifacts

Artifacts are concise, structured, and generated only when their information is needed.

### Intent record

- Problem and affected users or systems
- Observable outcome
- Non-goals
- Constraints and invariants
- Unresolved questions
- Risk and uncertainty

### Decomposition graph

- One-sentence purpose for each slice
- Dependencies and ordering
- Acceptance claims
- Expected review boundary

### Decision log

- Consequential decisions the human participated in
- Alternatives considered
- Accepted assumptions
- Deviations discovered during implementation

### Evidence manifest

- Exact repository revision
- Acceptance claim identifiers
- Evidence for each claim
- Verification identity and result
- Known gaps or exclusions

## Framework layers

### Interactive layer

OpenCode hosts design discussions, follow-up questions, artifact review, and explicit transition
requests. Agents, skills, and commands shape this experience.

### Optional local control layer

If observed failures justify stronger controls, an OpenCode plugin and custom tools can own workflow
state, check transition policy, and reject disallowed operations. This is a possible later layer,
not an initial requirement. Durable state must live outside an OpenCode session if this layer is
added.

### Evidence layer

The framework records checks and approvals against immutable revisions. A new revision invalidates
stale evidence according to policy.

### Repository enforcement layer

Required CI checks and branch protection can prevent merges that bypass the local workflow. This
layer is optional during early experiments but required before claiming enforcement outside
OpenCode.

## Possible enforcement guarantees

If future use requires hard enforcement, the mature framework may guarantee that:

- Implementation cannot start before its required intent and slice approvals.
- Generated work cannot silently become executable.
- Required evidence exists for the exact revision under review.
- Stale approval and verification are detected after changes.
- The implementing agent is not the sole verifier when policy requires independence.
- Merge or deployment is blocked when repository enforcement is configured and policy is unmet.

## Non-guarantees

The framework cannot guarantee that:

- A human genuinely understood a proposal after approving it.
- Requirements, architecture, tests, or reviewer conclusions are correct.
- Independent agents do not share blind spots.
- Work performed outside every configured enforcement point follows the lifecycle.

The framework should make passive approval visible and less convenient, keep the reviewed material
small, and require active human participation for high-risk decisions. It cannot inspect a person's
mental state.

## Initial direction

The first version should improve the existing interactive workflow without a plugin or custom
enforcement:

1. Discuss the problem and design normally.
2. Present intent and unresolved decisions in small, reviewable pieces.
3. Stop before converting the discussion into issues or implementation.
4. Review and revise the decomposition interactively.
5. Implement one bounded slice at a time after explicit direction from the human.
6. Present focused evidence before continuing to another slice.

Grill with Docs should be piloted alone first because it directly tests interactive questioning,
shared language, and selective decision records. OpenSpec should be piloted separately afterward to
test durable change artifacts and repository-level state. GSD Core remains a later evaluation
target. Any custom implementation should address observed gaps rather than reproduce an existing
framework from scratch.
