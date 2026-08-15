# Agent Development Framework Research

- Status: Active research ledger
- Date: 2026-08-15
- North star: [Agent Development Framework](agent-development-framework.md)

## Research question

How can a software engineer use coding agents without allowing generation speed to exceed human
comprehension, judgment, and accountability? The desired framework must work across repositories,
machines, models, personal projects, and workplace environments.

## Summary

The research did not find one framework that combines interactive design, durable intent,
comprehension limits, deterministic lifecycle enforcement, independent verification, and portable
repository integration.

The most consistent effective pattern is a composition of:

- Human ownership of intent, architecture, risk, and acceptance
- Small execution units with explicit boundaries
- Durable, queryable workflow state
- Deterministic tests, hooks, policy checks, and permissions
- Verification separate from implementation
- Evidence tied to the exact revision
- Human approval at consequential transitions
- CI and source-control rules as final enforcement points

Spec-driven development can supply useful artifacts, but a specification by itself does not enforce
the lifecycle and can create a second review burden.

## Evidence about productivity and trust

### METR experienced developer study

METR ran a randomized study with 16 experienced open-source developers completing 246 real issues.
With early-2025 AI tools, participants took 19 percent longer despite predicting a 24 percent
speedup and continuing to believe afterward that they had been faster.

This result applies to experienced developers in mature repositories using the tools available at
the time. It does not establish that all developers, tasks, or newer models have the same outcome.

Source: <https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/>

### GitHub Copilot quality study

GitHub reported that Copilot users in a bounded web-server exercise were more likely to pass all
unit tests and received modestly better blind review scores. The task was constrained, short, and
vendor-sponsored, so it does not contradict the higher verification burden found in mature
repositories.

Source: <https://github.blog/news-insights/research/does-github-copilot-improve-code-quality/>

### Trust in generated code

Microsoft interviews with developers identified expectation setting, configuration, and validation
as recurring trust problems. The research supports calibrated trust based on evidence rather than
blanket acceptance or rejection.

Source: Microsoft Research publication index:
<https://www.microsoft.com/en-us/research/publication/>

Study: "Investigating and Designing for Trust in AI-Powered Code Generation Tools"

### Security and confidence

A controlled study found that participants using an AI assistant produced less secure code while
becoming more likely to believe their code was secure. More deliberate interaction and lower trust
in the assistant correlated with fewer vulnerabilities.

Source: <https://par.nsf.gov/biblio/10472235>

## Evidence about comprehension and review

### Review size

Microsoft analyzed 1.5 million review comments across five projects. The proportion of useful
comments decreased as the number of files in a change increased. The study establishes an
association, not a universal file or line limit.

Source: <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bosu2015useful.pdf>

### Modern code review

Research by Bacchelli and Bird found that review is also used to understand changes, transfer
knowledge, and consider alternatives. Defect detection is only one purpose of review. Agent review
can assist with defect detection but does not automatically preserve shared understanding.

Source: Microsoft Research publication index:
<https://www.microsoft.com/en-us/research/publication/>

Study: "Expectations, Outcomes, and Challenges of Modern Code Review"

### Automation bias

A systematic review of 74 studies found that workload, time pressure, trust, and prominent
recommendations can increase automation bias. Accountability and deliberate reasoning sometimes
improved vigilance, though most evidence came from healthcare decision support rather than software
development.

Source: <https://pmc.ncbi.nlm.nih.gov/articles/PMC3240751/>

No reviewed research established a reliable numeric limit for specification size, diff size, or
review duration. The framework must use configurable budgets and observed comprehension rather than
claiming a scientifically optimal threshold.

## Practitioner experience

### OpenAI harness engineering

OpenAI described an internal project with roughly 1,500 merged pull requests and no manually written
code. Its useful mechanisms included small design and implementation units, checked-in execution
plans, isolated worktrees, specialized review agents, structural tests, custom linters, browser
automation, logs, metrics, traces, and screenshots.

The team reported that one large instruction document failed because instructions competed for
context, became stale, and were difficult to verify. OpenAI also reported spending about 20 percent
of each week cleaning up low-quality agent output before adding more mechanical quality controls.

Source: <https://openai.com/index/harness-engineering/>

This is a vendor account from an unusually instrumented environment. Its mechanisms are more
transferable than its throughput claims.

### Anthropic Claude Code guidance

Anthropic recommends interactive planning for uncertain or multi-file work, skipping planning for
obvious changes, keeping persistent instructions short, loading context on demand, and giving the
agent pass or fail signals. Stop hooks can prevent completion while deterministic checks fail.
Fresh-context reviewers provide additional evidence but may over-report findings.

Source: <https://www.anthropic.com/engineering/claude-code-best-practices>

### HumanLayer workflow evolution

HumanLayer reported that reviewing a large generated plan instead of code did not work. Reviewers
still needed to inspect the implementation and had to keep both the plan and diverging code in
mind. Its later workflow used shorter design discussions, structure outlines, and explicit human
approval points.

Source: <https://www.heavybit.com/library/article/whats-missing-to-make-ai-agents-mainstream>

HumanLayer has a commercial interest in approval and orchestration tooling. The reported failure is
still useful because it describes abandoning an earlier recommended practice.

### Beads and nested plan failure

Steve Yegge reported discarding a 350,000-line agent-built orchestration system, removing about
70,000 lines of plan management, and accumulating 605 Markdown plans. Nested plans lost coherence
after context compaction, while high agent concurrency created unsustainable merge queues. He
reduced concurrency and replaced prose plans with a structured dependency graph.

Source: <https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a>

This is a single practitioner's account and also promotes Beads. It supplies a concrete warning
about building a large framework before validating a small control loop.

### GitHub agent review

GitHub reported that broad repository exploration made its code-review agent more expensive and
less useful. Starting from the diff, forming specific review questions, and reading only targeted
context reduced average review cost by about 20 percent without an observed quality regression.

Source: GitHub Copilot engineering blog:
<https://github.blog/ai-and-ml/github-copilot/>

Article: "Better tools made Copilot code review worse. Here's how we improved it."

## Spec-driven development findings

Current spec-driven systems commonly separate:

1. Project principles and constraints
2. Problem and observable behavior
3. Clarification and codebase research
4. Technical design
5. Task decomposition
6. Incremental implementation
7. Verification and archival

Useful specifications are concise, behavior-focused, testable, explicit about non-goals and
important failure cases, and divided into independently verifiable work. Large agent-authored plans
can duplicate the code, hide decisions, drift from implementation, and become harder to review than
the change itself.

### Independent evaluation

Martin Fowler tested Kiro, GitHub Spec Kit, and Tessl. A small Kiro bug became four user stories and
16 acceptance criteria. A medium Spec Kit feature produced repetitive Markdown that was tedious to
review, and research notes were misread as new requirements. He preferred reviewing code in that
experiment and questioned one prescribed workflow for all task sizes.

Source: <https://www.martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html>

### GitHub Spec Kit community reports

Community reports include both successful use on substantial work and failures involving excessive
analysis, unnecessary files and tests, rigid stages, and dense documentation. Several users arrived
at a lighter workflow for small changes and deeper structure only for uncertain or multi-part work.

Sources:

- <https://github.com/github/spec-kit/discussions/1784>
- <https://github.com/github/spec-kit/discussions/152>

## Existing tools

Adoption signals below were observed on 2026-08-15. Stars indicate attention, not active use or
quality.

### OpenSpec

- Repository: <https://github.com/Fission-AI/OpenSpec>
- Documentation: <https://openspec.dev/>
- Observed version: 1.9.0, released 2026-08-13
- Approximate adoption: 65,000 stars
- Supports more than 30 coding tools, including OpenCode
- Stores proposals, designs, tasks, requirements, verification, and archives in the repository
- Provides an interactive explore and proposal flow
- Uses schemas and lifecycle commands but has no formal human approval record
- Agents and users can bypass its intended sequence through ordinary tools

OpenSpec is the strongest candidate for evaluating durable change artifacts. Its main fit question
is whether repository-level specifications improve comprehension or create excessive material.

### GSD Core

- Repository: <https://github.com/open-gsd/gsd-core>
- Documentation: <https://opengsd.net/>
- Observed version: 1.10.0, released 2026-08-08
- Approximate current repository adoption: 8,300 stars
- The archived predecessor had approximately 65,000 stars
- Supports OpenCode and several other coding tools
- Uses discuss, plan, execute, verify, and ship stages
- Preserves state, context, phase plans, verification, and fresh subagent work
- Most lifecycle enforcement remains prompt-based

GSD Core is the strongest candidate for evaluating an interactive staged experience. Its phase
model and recent repository transition create adoption and maintenance risk.

### GitHub Spec Kit

- Repository: <https://github.com/github/spec-kit>
- Observed version: 0.16.4, released 2026-08-14
- Approximate adoption: 129,000 stars
- Supports constitutions, requirements, clarification, plans, tasks, and implementation
- Uses durable artifacts and broad tool support
- Does not prevent stages from being skipped
- Has substantial reported risk of artifact volume and ceremony

Spec Kit is a useful source of patterns but is not the first pilot candidate for a developer already
experiencing specification and review overload.

### BMAD Method

- Repository: <https://github.com/bmad-code-org/BMAD-METHOD>
- Observed version: 6.11.0, released 2026-08-10
- Approximate adoption: 52,000 stars
- Covers product briefs, requirements, architecture, stories, testing, and retrospectives
- Uses specialized roles and adaptive workflow depth
- Primarily enforces behavior through prompts and generated artifacts

BMAD is mature but has more roles and ceremony than the initial framework should adopt.

### Beads

- Repository: <https://github.com/steveyegge/beads>
- Observed version: 1.2.2, released 2026-08-15
- Approximate adoption: 26,000 stars
- Supplies a durable dependency graph, work readiness, ownership, and audit history
- Does not govern intent, architecture, acceptance, or comprehension

Beads may be a future task-state component but is not a complete development framework.

### HumanLayer

- Workflow: <https://docs.humanlayer.com/explanation/workflow-phases>
- Uses explicit design and implementation checkpoints
- Current open-source components are fragmented between skills and an alpha control plane
- The control plane introduces substantial infrastructure and commercial coupling

HumanLayer is a source of approval and interaction patterns rather than an initial dependency.

### Grill with Docs

- Page: <https://www.aihero.dev/grill-with-docs>
- Source: <https://github.com/mattpocock/skills>
- Distributed as a small skill rather than a standalone framework
- Conducts an interactive design-tree interview before implementation
- Records domain language in `CONTEXT.md` and selected decisions as ADRs
- Leaves most answers in conversation history
- Has no workflow state, verification, approval record, or deterministic enforcement
- Uses generic skill installation rather than a native OpenCode integration

Grill with Docs is a strong candidate for the interactive design layer. It addresses the current
comprehension problem more directly than the larger lifecycle systems. Its default questioning is
round-based, so a pilot must determine whether each round remains small enough to absorb.

It depends on separate `grilling` and `domain-modeling` skills. The installer does not currently
guarantee those dependencies. Reports also describe lost decisions after context compaction and
unreliable artifact writing when Grill is invoked through OpenSpec orchestration.

Sources:

- <https://github.com/mattpocock/skills/issues/475>
- <https://github.com/mattpocock/skills/issues/669>
- <https://github.com/mattpocock/skills/issues/853>

### Other surveyed tools

Agent OS, Taskmaster, Kiro, and Tessl were also reviewed. Agent OS focuses on standards and prompts.
Taskmaster focuses on generated task management. Kiro provides an integrated proprietary IDE and
hooks. Tessl's broader framework remained in limited availability. None met the complete
portability, interaction, comprehension, and enforcement requirements.

## OpenSpec pilot details

OpenSpec integrates with OpenCode by generating repository-local skills and commands. It does not
run as an OpenCode plugin, daemon, or policy engine.

Minimal initialization:

```sh
npm install -g @fission-ai/openspec@latest
openspec init --tools opencode --profile core
```

Generated structure:

```text
openspec/
  specs/
  changes/
  config.yaml
.opencode/
  skills/
  commands/
```

The main interaction is:

```text
/opsx-explore
-> interactive investigation, no artifacts or code
/opsx-propose
-> proposal, design, tasks, and requirement artifacts
[ordinary conversation and revision]
/opsx-apply
-> implementation
/opsx-archive
-> merge current specifications and archive the change
```

OpenSpec deliberately stops proposal generation before implementation, but this boundary is an
instruction rather than a formal approval lock. Verification is optional and does not always block
archival. Validation can be bypassed with explicit command options.

The OpenSpec pilot should use it alone on one small but meaningful change. It should evaluate:

1. Whether the interactive design discussion remains useful
2. Whether the proposal can be understood without skimming
3. Whether generated artifacts preserve the human's actual decisions
4. Whether implementation remains bounded and reviewable
5. Which expected controls OpenSpec does not enforce

OpenSpec and GSD Core should not be combined during their initial evaluations because attribution
would be unclear.

## OpenCode as a framework host

Official documentation:

- Agents: <https://opencode.ai/docs/agents/>
- Commands: <https://opencode.ai/docs/commands/>
- Skills: <https://opencode.ai/docs/skills/>
- Plugins: <https://opencode.ai/docs/plugins/>
- Permissions: <https://opencode.ai/docs/permissions/>
- Custom tools: <https://opencode.ai/docs/custom-tools/>
- Configuration: <https://opencode.ai/docs/config/>

### Guidance mechanisms

Agent prompts, command templates, skills, and repository instructions guide model behavior. OpenCode
can control whether an agent or skill is available, but their natural-language content is not an
enforcement boundary.

### Local enforcement mechanisms

OpenCode permissions can allow, ask, or deny access to tools. Explicit denial remains effective in
automatic mode. Agent-specific permissions can restrict delegation and mutation capabilities.

Plugins receive `tool.execute.before` and `tool.execute.after` hooks. A before hook can inspect or
change arguments and can reject a tool call by throwing an error. The current plugin API can also
participate in permission decisions. Custom tools can own explicit workflow transitions and access
durable state.

### Limitations

- Plugins execute in the OpenCode process and are trusted code.
- OpenCode permissions govern known tool dispatch, not every side effect of an allowed shell.
- Session continuation and compaction are not integrity-protected workflow persistence.
- Plugin memory has no documented durable persistence guarantee.
- Project configuration may override parts of global configuration.
- A person can bypass local controls by leaving OpenCode or disabling the configuration.

OpenCode is therefore suitable as the local interaction and control layer. It should not be the
only enforcement point once merge or deployment guarantees matter.

## Transferable enforcement patterns

### State machines

Declarative workflow engines show how named states, guarded transitions, parallel checks, and
terminal failures make incomplete work explicit.

Source: <https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html>

### Policy as code

Open Policy Agent evaluates declarative policy against structured input and can return failure to a
CI caller. It separates the lifecycle from the rules governing each transition.

Source: <https://www.openpolicyagent.org/docs/cicd>

### Evidence and provenance

SLSA provenance binds claims to builders, inputs, processes, and artifacts. It does not prove
correctness, but its model is useful for binding verification evidence to a revision and producer.

Source: <https://slsa.dev/spec/v1.0/levels>

### Source-control enforcement

Required checks, code-owner approval, stale approval dismissal, deployment environments, and branch
protection can enforce repository transitions. These mechanisms do not determine whether intent or
acceptance is semantically correct, so they must consume evidence from the framework.

## Open questions

- Where durable workflow state should live before repository CI integration
- Which transitions require active human explanation rather than simple approval
- How to classify risk without letting an implementing agent lower it
- How to define a practical comprehension budget without arbitrary universal limits
- Whether repository-local intent artifacts remain useful after implementation
- How workplace policy and identity should override personal defaults
- How independent verification should differ by risk and repository type
- Which OpenSpec concepts survive a pilot without importing its full artifact lifecycle

## Current direction

The next work is evaluation, not framework implementation. Preserve this research ledger as
evidence and keep the north star concise. Pilot Grill with Docs first to evaluate interactive
design, then pilot OpenSpec separately to evaluate durable change artifacts. Decide what to adopt,
adapt, or build only after observing both.
