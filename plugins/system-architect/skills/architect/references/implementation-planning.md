# Optional implementation-planning profiles

These are output profiles of [architect](../SKILL.md), not independent planning systems. Load only the requested profile. Existing approved specifications, project formats, requirement IDs, and the architect's authorization/evidence rules remain canonical.

## Shared intake and output rules

Read the relevant approved objective/specification, current source, existing commands/interfaces, accepted constraints, and prior decisions. Use actual repository evidence when available, not just supplied prose. Mark missing facts as unknown and distinguish assumptions from approved requirements. Do not fabricate paths, APIs, commands, dates, assigned people, metrics, or completion status.

Select **epic** for total scope and work packages, **milestone** for one implementable slice, or **roadmap** for sequencing and dependency decisions. Create only the requested artifact, in the requested destination/format. A planning request does not authorize implementation; an existing authorized implementation request does not become document editing just because a plan is attached.

Reuse existing IDs and trace each committed requirement to a component/interface, task/work package, and observable acceptance. A dependency states the actual input that must exist and what it blocks. Label proposed sequencing/preferences separately from confirmed technical dependencies. Shared files or state can prevent supposedly independent work from being parallel.

Each meaningful unit states what changes, what must not change, its observable result, and how that result can be checked. Choose validation from the actual request/project contract; distinguish source inspection, structural checks, manual/runtime observations, and explicitly requested automated checks. Do not impose tests-first, new tests, or a generic hardening phase.

Keep rollback/restore and continuation details proportionate to actual risk. Do not invent infrastructure, a rollout program, or operational artifacts for a text-only change. Keep one canonical explanation of shared constraints rather than repeating them in every section.

## Epic — bounded objective and work packages

Use when the objective spans multiple independent slices and the question is what the complete work includes.

Capture the problem, desired outcome, current implementation context, scope/non-goals/negative constraints, committed requirements, and technical responsibility boundaries. Explain material alternatives only where a decision remains relevant.

For each work package provide:

| Field | Content |
|---|---|
| Goal and scope | Concrete capability/change and preserved behavior |
| Owner/boundary | Actual responsible component/interface; assigned person only if known |
| Changes | Existing/target files or interfaces established from evidence |
| Dependencies | Required outputs/contracts and blocked consumers |
| Acceptance | Observable result tied to committed requirements |
| Verification | Real known command/manual procedure and expected signal, or a precise unresolved check |
| Handoff | What the next implementer receives and may assume; relevant rollback/continuation limits |

Prefer independently reviewable packages that leave the system coherent. Give only enough coarse order to explain prerequisites. Do not automatically create a formal roadmap, all milestone documents, or an execution ledger. For one small slice, explain that the milestone-sized plan is sufficient without expanding the user's scope.

## Milestone — one executable bounded slice

State objective, inputs/prerequisites, allowed scope, forbidden changes, current-versus-target behavior, and the accepted requirement/epic references. Specify necessary interfaces, error/failure behavior, data/compatibility constraints, and step order from actual dependencies.

For each action name the target, exact change, input assumptions, expected visible outcome, and verification evidence. Do not use “implement the rest” or make the next agent rediscover known interfaces. Keep assumptions and blocking unknowns visible.

Define observable exit criteria and what the following slice can rely on. For a risky change, include the actual stop/rollback/disable or continuation mechanism and what it cannot restore. A milestone may finish with known deferred scope only when the agreed slice excludes it; it must not call partial committed scope complete.

A complete plan records **expected** evidence. A later implementation handoff records **observed** results. Do not pre-fill success, mark acceptance passed, run code, or start the next milestone from planning authority alone.

## Roadmap — dependency-first sequencing

Derive phases/milestones from the work rather than a fixed taxonomy or count. Use actions/tasks instead of ceremonial phases when the work is a single pass. No required phase zero, foundation, hardening, rollout, or cleanup section unless the actual project needs it.

For each phase/slice capture its outcome, inputs/dependencies, deliverables or working state, observable exit, unresolved decision, and what failure changes about the next action. Identify the next executable slice and why its inputs exist. Give dates only when supported; distinguish estimates from commitments.

Separate a **decision gate** (what evidence permits continuing) from a **verification procedure** (how that evidence is obtained). Where rollout/migration matters, show actual ordering, compatibility, activation and restore boundaries without duplicating a second operational plan. Explicitly identify a shared dependency that changes the proposed sequence.

## Final review

Check source/requirement traceability, concrete targets and interfaces, real versus proposed dependencies, observable exits, preserved scope/compatibility, and exact remaining unknowns. Match the requested artifact and granularity; no fixed 15/18-section skeleton and no automatic epic + milestone + roadmap bundle. A complete-looking document with blocking unknowns is not implementation-ready.
