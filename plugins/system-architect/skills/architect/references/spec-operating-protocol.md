# Architecture SPEC Operating Protocol

Use within the route selected by SKILL.md. This reference defines execution and engineering detail, not independent routing or mandatory subsystems. `templates.md` owns output shapes; `checklists.md` owns completion checks.

## Contents

- [Source intake](#source-intake)
- [Architectural change lens](#architectural-change-lens)
- [Session execution](#session-execution)
- [Recovery and change impact](#recovery-and-change-impact)
- [Background](#background)
- [Requirements](#requirements)
- [Method](#method)
- [Architecture decisions](#architecture-decisions)
- [Implementation](#implementation)
- [Milestones](#milestones)
- [Gathering Results](#gathering-results)
- [Review and update](#review-and-update)
- [Authorized implementation](#authorized-implementation)
- [Readiness and delivery](#readiness-and-delivery)

## Source intake

Establish the goal, requested action, deliverable, scope, delivery mode, source revision, and applicable constraints before drafting. Keep this working context in the conversation; a new tracking file is not required.

For an existing project, inspect the actual entrypoints, affected components, schema/interfaces, configuration, dependencies, and available runtime evidence. Follow the path from user action to persisted result; a module's existence does not establish that it is wired or reachable. Read enough surrounding code to understand callers, state ownership, failure paths, and compatibility.

For multiple archives or revisions:

1. Identify each archive's root, contents, role, and visible version evidence. Do not treat the largest archive, latest-looking filename, or latest timestamp as authoritative by itself.
2. Respect an explicitly selected base. Otherwise use the stated project/version and compare conflicting material before resolving precedence. Keep approved requirements separate from what code currently does.
3. Compare behavior and unique requirements as well as paths. A copied file can still contain incomplete workflows; a renamed file can be the same content. Do not replace newer working rules with an older example's defaults.
4. For a merge, integrate unique applicable content into its canonical owner; keep conditional details conditional. Do not concatenate conflicting instructions, duplicate optional-section templates, or package an archive inside an archive.
5. Carry unexplained conflicts forward explicitly. Make independent changes where the intent is clear; do not guess away a material user decision.

### Source lineage and patch integration

Distinguish a full snapshot, an incremental patch, a cumulative patch, a reference-only package, and an explicit replacement base from their content and stated role. A version suffix is not proof of any of these. Determine the base and prerequisite changes for each delta; check changed paths and surrounding content, including renames, deletions, and binary/configuration changes. A patch against the original tree is not automatically applicable after another patch.

Reconstruct the selected working tree before editing. Preserve earlier accepted changes unless the user explicitly replaces them or the chosen new base demonstrably includes them. Apply deltas to a working copy using their actual prerequisites; a partly applied patch or unresolved conflict is not a completed integration. Do not force a rejected hunk or silently drop it. Reconcile overlapping changes by behavior and contract, not by concatenating files. For divergent branches, use the common base when available; without it, preserve unique work and expose unresolved precedence.

Compare the assembled result with both the selected base and the affected prior work. Classify each disappearance as an intentional removal, a relocation, a superseded implementation, or an unexplained loss. Resolve unexplained loss before declaring a cumulative result. Keep this reasoning in the current task context; do not create an inventory or provenance bundle.

For selective improvement, accept a source addition only if it fixes a concrete gap, improves an observable outcome, or clarifies an ambiguous contract without breaking the base's constraints. Decide whether to reuse, adapt, or omit it, and integrate it into the existing canonical owner. Compare triggers, outputs, failure paths, examples, and exclusions, not just paragraph overlap. A larger source pack is not automatically a better plugin. Preserve working behavior; do not import duplicate instruction variants, evaluation machinery, provider stubs, or a new runtime merely to claim coverage.

For decision-changing evidence gaps, use `decision-evidence.md`. Keep source support separate from readiness: a well-cited design is not implemented source, and a local successful operation does not prove an external service guarantee.

Treat code as evidence of implemented source behavior, runtime observations as evidence for their exact environment, and the approved SPEC as the target contract. When they disagree, describe the gap rather than silently redefining one as the other. Cite supplied source locations or links using the host's supported citations; never manufacture line numbers, commit IDs, or completed reads.

## Architectural change lens

Architecture controls direction, not scope. Use the smallest accurate current-state model and the smallest complete change that satisfies the authorized goal. Do not produce a separate architecture document for a local correction.

| Change surface | Required depth |
|---|---|
| Local implementation without material contract, state, or deployment impact | Identify the responsible owner and violated or preserved invariant; inspect the actual caller; implement directly without another authority or parallel path. |
| API, event, schema, configuration, ownership, dependency, or shared-state boundary | Trace producer and consumer expectations; name the target owner, authoritative state, invariants, and affected call paths before changing the contract. |
| Durable data, independently deployed consumers, runtime topology, or multiple subsystems | Also account for intermediate states, mixed versions, rollout, recovery, rollback limits, cutover authority, and retirement of the obsolete path. |

**Orient.** Follow relevant entrypoints through control/data flow to the authoritative state. Locate the invariant's owner, current consumers, accepted constraints, and available operational evidence. Distinguish intentional constraints from historical accidents; names and directory layout alone do not prove responsibility. When only part of the system is inspectable, bound the model rather than asserting repository-wide coverage.

**Name the target form.** Make clear which concepts and responsibilities remain, which owner enforces each important invariant, which path is authoritative, and what duplicate or obsolete concept disappears. A cache, projection, replica, or adapter may be valid, but its authority and reconciliation relationship must be explicit. Multiple legitimate writers need a defined coordination contract, not an accidental second source of truth.

**Choose proportionally.** Prefer a change within the current owner, then an established appropriate pattern, then a narrow boundary or adapter. Introduce a shared abstraction for demonstrated shared meaning or volatility, not imagined extensibility. Correct an inappropriate existing pattern at the smallest relevant boundary rather than copying its defect or redesigning unrelated modules. Consider where the next similar capability belongs and what repeating this pattern would do to coupling, operations, and removability; do not invent future product requirements.

**Converge without losing behavior.** For a rewrite or migration, map observable current capabilities to their target paths, identify authorized changes/removals, and retain unresolved gaps. Fewer lines or a new implementation beside the old one proves neither preservation nor migration completion. A temporary wrapper, fallback, alias, or dual path needs a specific consumer, bounded authority, divergence handling, and an observable exit condition. Do not remove a still-required compatibility path merely to make the design look simpler. Use [migration contracts](implementation-patterns.md#migration-and-compatibility) and the capability mapping in `templates.md` when that work is in scope.

**Execute and reconcile.** Put behavior with the owner of the invariant and keep policy separate from transport/UI/storage details unless those details are part of the requirement. Update affected consumers and contracts, not just the declaration. If implementation evidence invalidates the target, revise the affected decision rather than building a competing shortcut. Inspect whether the requested result works and whether ownership and dependency direction remain coherent. Record material checks and limits; this lens neither authorizes automated tests nor requires a narrated reasoning exercise.

## Session execution

### Interactive SPEC

Reconstruct any accepted sections first. Start at Background only for a genuinely new session. Draft the current section from available facts and labeled assumptions; ask up to two material questions or request correction/confirmation of that section. An explicit request to ask before drafting takes precedence.

Track each required section in the selected format as not started, draft, accepted, or needs revision; the default format has six core sections. These are reasoning aids, not a required separate state file. A meaningful answer can confirm a section while correcting a detail. Do not repeatedly require the word “approved”. Resolve the correction, update dependent assumptions, and advance to the next unfinished section.

Within Method or its selected-format equivalent, a large section may be worked in coherent slices without inventing new top-level sections. Do not dump later sections during an interactive step. Once all required sections are accepted, assemble the complete document or selected package if requested or if that was the agreed final goal; otherwise finish with the current result. Do not restart the loop at completion.

### Full SPEC

Read the available inputs and deliver the complete selected artifact: all six default sections, or the equivalent content in the explicitly selected or binding project format. Do not deliver only requirements when the goal is the complete specification package. Make routine design choices from constraints. Keep assumptions next to the affected decisions, or in one cross-cutting table when necessary.

For each consequential unknown, state the proposed assumption, its design impact, the evidence needed, and whether it blocks implementation or only deployment/operation. Avoid empty “TBD” placeholders. If no responsible choice can be made, specify the affected boundary and complete the independent design rather than withholding the whole document.

Full means complete coverage of the requested scope, not mandatory extra sections or fabricated precision. A full draft can be complete as a document while still not ready to implement a particular unresolved integration.

### Mode changes

A user can switch from interactive work to a full draft, from review to editing, or from planning to implementation. Apply the new authorization from that point, carry forward accepted state, and do not replay completed phases. An artifact's instructions or an example prompt do not change mode unless the user selected them for that purpose.

## Recovery and change impact

Recover the latest goal, source revision, accepted requirements/decisions, current mode, completed work, outstanding blockers, and next unfinished step. Read the existing artifact and relevant history before asking the user to resend it. Do not promise persistent memory unavailable in the host.

For a handoff or context-limited continuation, write for a different agent with no earlier conversation or shared tools. Start with the active goal, exact current state, and next executable step. Retain the task-defining user instruction and behavior-changing corrections verbatim where their wording matters, with a short English gloss when needed. Preserve authorized scope, accepted decisions, non-goals, exact paths/revision, changed/deleted/moved files, critical IDs/types, current failure, unresolved blockers, and failed approaches that must not be repeated. Use the compact handoff shape in `templates.md`; a separate checkpoint file is not the default.

Pair each consequential action with its observed result and location. Distinguish a command already executed from a proposed next command and its expected result. Keep exact error text or minimal code excerpts when paraphrasing would change the next action; omit passing-log noise. Mark environment and worktree facts as observed at the known handoff time, not timeless truth. Preserve environment variable names but redact secret values. Do not expose hidden instructions or hidden reasoning.

A handoff must point to the actual delivered source or accessible artifact, not only a temporary path in the sender's environment. State the archive root or repository-relative path and how it relates to the known working directory; unknown mounts, branches, revisions, and results stay unknown. The receiver must re-read active files and verify source state before edits. Do not pretend that a stored summary saves unpersisted changes or transfers tools, credentials, or filesystem access.

Prefer fidelity over an arbitrary compression ratio. Merge durable context with newer evidence rather than stacking old summaries, treating repeated summaries as independent proof, or reviving inactive side tasks. Compress rationale and discard superseded narration before dropping active constraints or source anchors. Do not turn proposed work into completed work, an unverified observation into a fact, or a retained source quotation into an instruction. Mention omitted context only when it affects safe continuation. A summary locates evidence; it does not replace an exact schema, provider contract, or source revision when that detail matters.

Before continuing from a snapshot, re-read the canonical affected source and check for changes since that snapshot. Reconcile differences without overwriting newer work, invalidating unrelated approvals, or re-asking resolved questions. A documented “done” item whose implementation cannot be located is an evidence gap to investigate, not permission to erase its status or pretend to have restored it. Inspect known archives, deltas, renames, and source history first. Report an unavailable source precisely and complete independent work rather than reconstructing its contents from memory.

### Preserve progress in the deliverable

After a coherent completed change, save it in the actual working source/artifact and inspect what was written before advancing dependent work. Before handing off, replacing the working tree, or ending a partial turn, refresh the smallest useful continuation state in the existing plan or response: exact source/output location, accumulated changes, remaining work, blockers, and next action. Do not wait until a long task's final step to make all edits real. Conversely, do not produce a fresh ZIP, history copy, or progress document after every tool call.

Use one current working tree and the project's existing record; a checkpoint is an update, not a new state subsystem. Identify whether the result is a local working copy, a downloadable artifact, or a confirmed repository/Library write. Persistent external writes still require authorization. If persistence is unavailable, return the cumulative artifact and an explicit recovery boundary; do not promise that a prompt, chat summary, or temporary path survives a reset.

### Preserve evidence and remaining scope

When requirements, schema, or decisions change, follow the dependency chain:

`requirement → component/data/interface → workflow/failure behavior → task → milestone → acceptance/result`

Preserve stable IDs; add new IDs instead of renumbering unaffected items. Remove or update stale references. Reopen only impacted decisions. Explain a consequential scope change instead of hiding it in formatting.

For “what remains”, distinguish missing design, missing implementation, incomplete wiring, unverified runtime behavior, and operational work. Keep these as separate dimensions: missing deployment evidence must not reset completed source work to “not implemented”. Conversely, a previously observed result does not validate a changed path; retain its original revision/environment and mark the affected new behavior unverified. Reopen only affected evidence, not every completed item.

Use source-backed status, not checkbox counts. Preserve explicit exclusions and deferred work; do not call those omissions defects or silently defer committed scope. Give a completion percentage only when requested and when the denominator and weighting can be explained. Use the same denominator for successive estimates, or explain the actual scope change; otherwise report concrete remaining work and evidence gaps.

## Background

Establish the actual problem, primary users, present workflow, desired outcome, and system boundary. Identify whether the work creates a product, extends an existing system, or replaces one. Carry forward constraints already supplied: deployment environment, team, deadline, cost, integrations, data volume, and compatibility.

For a vague idea, ask about the user and successful outcome before choosing infrastructure. In Interactive SPEC, draft Background from the available evidence and ask only the next consequential question. In Full SPEC, state reasonable assumptions alongside the affected design and identify what would change if they are wrong.

Lean scope means a small but complete end-to-end workflow. It does not mean mocked core functionality, incomplete wiring, lost data integrity, or a UI that cannot perform the promised task. Never silently convert a production requirement into a prototype. Preserve explicitly excluded features.

## Requirements

Use stable requirement IDs where traceability would otherwise become ambiguous. Apply MoSCoW to user/system outcomes, not to implementation tasks:

| Priority | Meaning |
|---|---|
| Must Have | Launch cannot meet its stated purpose without this outcome |
| Should Have | Important, but delivery can succeed without it initially |
| Could Have | Useful optional enhancement |
| Won't Have | Explicit exclusion for this delivery |

Define actors, triggers, expected behavior, and observable success for core requirements. Include relevant non-functional constraints with an operating scenario: workload, data size, concurrency, latency, availability, recovery, or deployment limit. Record an unknown target as an assumption or open decision; never turn an illustrative number into a requirement.

For a non-functional requirement, connect the stimulus/actor, operating condition, affected workflow/component, expected response, and measurable limit or named unknown. Prioritize conflicting quality goals explicitly; a desirable average cannot compensate for violating a hard requirement.

Avoid "fast," "secure," "scalable," or "good UX" without a concrete implication. For example, define which workflow must work on mobile and what the user must be able to complete. Include authorization or isolation requirements when part of the supplied system's contract; do not add authentication, roles, tenancy, analytics, or audit logging to every product by default.

Map each Must Have to Method, Implementation, and a milestone acceptance criterion. Resolve incompatible Must Haves explicitly. Keep future possibilities in Should/Could or outside the current scope rather than implementing them preemptively.

For non-trivial behavior, state acceptance in a form such as “When <trigger>, while <precondition>, <owner> shall <observable response> within <relevant bound>.” Include refusal/invalid-input or failure behavior where it changes the contract. A user story can explain value but does not replace acceptance. Separate invariants that must always hold from operational targets with measurement windows and exceptions. Name the enforcing owner and the observation that would show a violation; “robust”, “simple”, and “works correctly” are not acceptance criteria.

Keep requirement priority separate from normative force: MoSCoW selects scope; a hard MUST NOT or invariant constrains every in-scope implementation. Preserve existing requirement and acceptance IDs across edits and map affected tasks to the precise criteria. Do not mandate a glossary, EARS syntax, user story, or dependency diagram for every small change; use them when they remove real ambiguity or the selected format requires them.

## Method

Select only the subsections needed to implement the requirements. For a CLI, local utility, or narrow library, specify commands or library interfaces instead of inventing a web API, database, workers, or tenancy.

### Similar systems

Research analogous systems only when their workflows, integration patterns, or constraints reduce a specific uncertainty. Use current official sources for changing technical claims. Explain the relevant pattern and why it fits; do not infer a product's private architecture from its public UI. Borrow a useful pattern without importing the mature product's entire feature set.

State which requirement or decision each borrowed pattern serves and what not to copy. Compare only relevant roles/workflows, data/ownership, integration behavior, or operating constraints; do not turn this into a market survey. Apply `decision-evidence.md` when source quality, conflicting contracts, or comparable measurements affect the choice.

### Architecture and components

State the chosen architecture, component responsibilities, owned data, public boundaries, dependencies, communication paths, and deployment shape. Make clear where validation, transactions, orchestration, and side effects occur. Keep domain and technical terms consistent across prose, diagrams, schemas, and APIs.

Start from the existing repository's patterns for a change to an established system. Introduce a new boundary only where a requirement justifies it. Prefer simple, reversible choices while uncertainty is high. The decision rules below are design defaults for this plugin, not external standards.

Use diagrams when relationships, branching, or ordering are clearer visually. Use the host's supported rendered format; provide PlantUML when requested or used by the project. Keep labels aligned with the actual component names and include failure paths where they affect the design. For an interactive client, define draft, submitted, persisted, and selected-result state using “Interactive state and result ownership” in `implementation-patterns.md`; do not use a visual mockup as evidence of implemented bindings.

### Data model

When persistent state is required, define its representation concretely. For relational storage specify relevant tables, columns/types, keys, relationships, nullability, uniqueness, constraints, and indexes justified by access patterns. For document, file, or key-value storage define equivalent identity, shape, consistency, and lookup contracts.

Describe ownership and lifecycle: who writes a record, transaction boundaries, state transitions, deletion/retention when relevant, and compatibility with existing records. Specify tenant ownership only for an actual multi-tenant system. Explain how generated values and timestamps are maintained; a creation-time default does not by itself define update behavior.

For migrations, cover current and target shape, data conversion, backfill ordering, concurrent writes, cutover, consumer compatibility, and recovery where applicable. Mark which operations preserve IDs, permissions, and external references. Do not assume a schema rename or table swap preserves every dependent contract without evidence.

### Interfaces

For important APIs define method/path or operation, caller, authorization when applicable, request/response shape, validation, errors, and side effects. Include concise examples for non-obvious payloads. Define pagination, ordering, concurrency/version checks, idempotency, and compatibility only where the workflow needs them.

For CLI interfaces define command, flags, input/output formats, exit behavior, and failure messages. For library interfaces define arguments, return values, exceptions, sync/async behavior, and resource ownership. State where validation happens and which errors users can recover from.

Do not invent provider fields, SDK methods, command flags, status codes, or supported versions. Verify concrete third-party contracts against current official documentation; distinguish a proposed internal interface from an existing external API.

### Workflows and algorithms

Cover the primary end-to-end path from trigger to visible result, including persisted state and external effects. Specify important branches, state transitions, cancellation, timeout, partial completion, and retry behavior.

For algorithms explain inputs, outputs, invariants, decision rules, and practical complexity where it matters. Use pseudocode only when it resolves ambiguity that prose leaves open.

For asynchronous work define durable acceptance, scheduling, execution ownership, completion visibility, and terminal failure. If a database transaction and external enqueue must stay consistent, specify the delivery/repair mechanism instead of silently assuming atomicity.

### Jobs and integrations

Add background processing only for a concrete need such as long-running work, scheduled work, independent retries, or response-time constraints. Define job payload/reference, trigger, identity, timeout, retry eligibility and bounds, duplicate handling, side effects, failure storage, cancellation, and recovery relevant to that job. Do not retry an unsafe external mutation merely because the request timed out.

For each integration specify provider and purpose, call direction, credentials/configuration required by its documented API, payloads, relevant limits, failure behavior, and environment assumptions. For webhooks define event identity, duplicate/out-of-order handling, acknowledgment point, and state reconciliation when needed.

State what the user sees when a dependency is unavailable, how unfinished work is found, and whether a fallback changes the promised semantics. Do not promise provider behavior that has not been verified.

### AI and agent components

Include this only when a requirement actually uses a model, prompt, retrieval, or agent workflow. Define the component's task and caller, trusted instructions versus variable/source data, available tools and action authority, output/validation contract, failure handling, resource limits, and observable completion. Keep provider-specific claims verified. Use the conditional patterns in `implementation-patterns.md` and the compact contract in `templates.md`; a prompt is not a substitute for application validation, permission enforcement, or durable state.

### Access, operations, and reliability

Preserve the system's established authorization and data ownership contracts. When roles or tenancy are required, define the actor/action/resource relationship and enforcement boundary. Keep security content limited to requested scope and requirements; do not add an unrelated security-improvement backlog.

Select observability that answers concrete operational questions: which request or job failed, which dependency caused delay, whether data processing completed, and whether the primary user workflow succeeds. Specify correlation, errors, health signals, and relevant metrics without turning every project into a monitoring platform.

State expected load and practical bottlenecks, recovery behavior, and the evidence that would trigger a scaling change. Address backup/restore, deployment compatibility, and rollout/rollback when these affect the delivery. Define measurable recovery targets only if supplied or explicitly marked as proposed assumptions.

### Trade-offs

Explain the chosen approach's benefit, cost, and revisit trigger. Compare alternatives only on requirements that matter: ownership, transactions, latency, deployment independence, operational effort, cost, or compatibility. A reasonable existing design need not be replaced just because another pattern is fashionable.

## Architecture decisions

| Choice | Appropriate conditions | Cost to account for |
|---|---|---|
| Modular monolith | Small team, cohesive deployment, transactional domain, evolving boundaries | Keep module ownership and interfaces explicit |
| PostgreSQL | Relational data and transactions fit; no existing constraint favors another store | Schema evolution, access patterns, operational ownership |
| Background queue | Durable deferred work or independent retries are required | Delivery semantics, duplicate effects, scheduling, failure recovery |
| Microservices | Independent deployment/scaling or stable team/domain ownership is a demonstrated need | Distributed consistency, interfaces, operations, failure isolation |
| Serverless | Intermittent/event-driven work fits verified runtime and provider constraints | Cold starts, execution limits, state boundaries, vendor dependence |
| Event-driven coordination | Independent asynchronous consumers need loose coupling | Ordering, duplication, schema evolution, eventual consistency |
| CQRS | Read and write models have materially different needs | Projection lag, rebuilds, additional data paths |
| Event sourcing | Reconstructable history is a primary domain requirement | Event evolution, projections, correction semantics, operational complexity |
| Multi-tenancy | Organizations/workspaces share a platform with distinct ownership | Isolation, constraints, configuration, lifecycle and migration |

For a new server application without stronger constraints, consider a modular monolith first. Consider PostgreSQL only when persistent relational data is needed, and a queue only when asynchronous requirements warrant it. Do not inject this stack into scripts, libraries, or an existing architecture.

Ordinary CRUD does not require CQRS. Audit logs alone do not require event sourcing. Multi-tenancy is a product requirement, not a default. For shared-table tenancy, ensure ownership and uniqueness constraints reflect the domain; isolated databases or schemas need a concrete isolation or operational reason.

For a requested ADR or a consequential decision that needs a durable record, use [ADR lifecycle](design-gate.md#adr-lifecycle). Keep the decision in the current canonical artifact when a separate file has no unique purpose. A recommendation, accepted decision, implementation, and completed rollout remain distinct states.

## Implementation

Translate Method into ordered, actionable work. Each task should name its behavior change, affected component or known path, dependencies, and visible completion signal. Use verified paths when source is available; label proposed paths otherwise.

Sequence work by dependencies and deliver a usable vertical slice early. Cover applicable setup, schema/migration work, domain behavior, interfaces, user flow wiring, jobs, integrations, operations, and deployment. Include compatibility and rollout/recovery steps when modifying live data or consumer contracts.

Manual/runtime verification is the default: identify the operation to perform, expected visible result or persisted state, important failure path, and evidence to inspect. Follow SKILL.md's explicit-request rule for automated tests. Do not create test tickets, coverage targets, a generic hardening phase, or extra documentation as implicit deliverables.

For an existing system, describe the before/after behavior and preserve unaffected APIs, configuration, and data. A proposed implementation plan is not proof that the feature runs.

## Milestones

Group dependency-ordered tasks into useful delivery slices. Use only as many phases as the work needs; the labels Foundation, Core Workflow, Integrations, and Delivery are optional examples.

Each milestone needs scope, dependencies, a deliverable, and observable acceptance criteria. Tie criteria to requirements and specify how to check them manually or in the running system. Separate planned evidence from evidence already collected. Avoid phases that end at a UI skeleton while its promised workflow remains unwired.

A completion signal should be concrete: a user performs an action, the expected state persists, the intended result is visible, and a relevant failure can be recovered from. Do not equate static inspection, a successful build, or a passing check with runtime correctness.

## Gathering Results

Define how to evaluate the delivered system in operation: which requirement/outcome is measured, data source, workload or measurement window, target or baseline, and action if the result is unsatisfactory.

Use realistic project-specific signals such as successful workflow completion, job completion time, latency under a stated load, error rates, data consistency, or reduced manual effort. Do not fabricate universal latency/SLO targets or measured performance. Preserve unknown targets as decisions to resolve.

An acceptance criterion describes what must be observed; it does not require an automated test suite. Record verified results separately from planned measurements and note environmental limits that affect confidence.

## Review and update

1. Establish the actual version and scope of supplied material. Read its linked dependencies only when they affect a conclusion.
2. Trace important requirements through design, interfaces, tasks, and acceptance criteria. Compare claims with available code/runtime evidence.
3. For each substantive finding give location, trigger or conflicting statements, consequence, and a concrete correction. Mark assumptions and uncertain risks as such; do not present preference as defect.
4. Prioritize by impact on the actual product, plausible trigger/likelihood, affected scope, and reversibility—not file length, fashionable architecture, or generic enterprise expectations. Check missing paths, contradictory contracts, state/identity ownership, forward progress, deadline composition, recovery, migration compatibility, and implementation gaps. Review only the relevant domain, runtime, data, maintainability, or operator perspectives; do not simulate independent reviewers or assume that every perspective requires an agent.
5. When edits are requested, correct the artifact itself, preserve unrelated work, and recheck affected cross-references and documentation-dependent claims. Turn accepted findings into concrete corrections with dependencies and observable completion in the existing plan when a plan is requested or already governs the work; do not leave a findings list instead of authorized implementation.
6. Report what changed and what remains unverified. Do not create an extra review report unless requested.

Do not impose a finding count or infer “no defects” beyond the inspected scope. A supplied review is a report of observations, not an independent reproduction; identify what current code or runtime evidence still needs confirmation. Distinguish a root-cause correction from an adjacent concern that does not share the mechanism.

For evidence-heavy findings, apply `decision-evidence.md`: verify the exact assertion, preserve opposing evidence, separate impact from repairability, and fix the smallest affected boundary. A source-only behavioral change is a change/risk identified by inspection, not a demonstrated runtime regression. When editing instructions, compare the resulting routes, input/output contracts, authorization, missing-input behavior, and conditional loading with the previous version. Do not call fewer words an improvement if a necessary behavior was lost.

A correction to one section must propagate only to dependent sections. Reuse approved requirements and decisions. Reopen them only when new evidence reveals a contradiction or the user changes the goal.

## Authorized implementation

When the user asks to implement or fix, read the current source, not just the plan. Determine the reachable behavior, accepted target, existing interfaces, and constraints. Resolve source lineage before modifying multiple revisions. Work in dependency-ordered slices: implement the behavior and integration paths, save and inspect the change, exercise what the environment permits, then advance to the next implementable item. A first usable slice is a sequencing choice, not permission to end a request for full completion.

Keep an internal list of the remaining authorized obligations or use the existing plan. Do not create a plan merely to track a small fix. If a task is blocked, name its exact prerequisite and continue independent tasks. User interruption or a real access/context limit may require partial delivery; return all accumulated changes rather than only the latest slice, and distinguish unfinished implementation from unavailable verification.

Use the repository's real paths, configuration, dependency management, and runtime conventions. Distinguish required application code from operator-owned provisioning, credentials, deployment, and environment acceptance. An unavailable production environment does not justify leaving implementable code as a TODO or returning only another plan.

For each completion claim, identify what changed and what was observed. A UI element must reach its handler; the handler must call the intended service; configuration must load; state must persist; the output must be reachable by the user. Verify important failure and recovery behavior where possible. Do not run automated suites without the user's explicit request.

If execution is blocked, deliver the completed code/artifact and identify the exact remaining operation, environment prerequisite, and expected observation. Provide verified commands only when useful and available; do not invent deployment flags. Do not describe source-only work as a completed rollout.

## Readiness and delivery

Use these evidence levels consistently; they are not mandatory project phases:

| Claim | Evidence required |
|---|---|
| Complete draft | Requested scope and sections are covered; all assumptions and unresolved decisions are visible |
| Implementation-ready design | Every Must Have has coherent contracts and traceability; no undisclosed core design blocker remains |
| Implemented in source | Required code and integration paths exist in the inspected revision; no placeholder substitutes for core behavior |
| Runtime verified | Named operations were actually performed in the stated environment and produced the reported results |
| Operationally accepted | Required deployment, dependencies, recovery, and operational criteria were observed in the target environment |

Do not collapse these into a single “production-ready” label. Report the highest level supported and any boundary that materially affects use. A verification checklist is planned evidence until its actions have been performed.

Before handing over an artifact, check internal links, source references, names, IDs, types, states, task dependencies, and acceptance mappings. Reopen the generated file and confirm it contains the intended changes. For archives, inspect the final member list, required hidden files, and the cumulative content against the working tree. A valid ZIP alone does not prove that earlier work is included. Avoid caches, unrelated source copies, build output, or nested archives.

For source delivery, use the user's requested form. A full archive is the complete selected working tree including prior accepted changes; a patch is a delta with its exact base and prerequisites stated in the response or existing record. Do not silently return a partial overlay as a full archive, include both forms by default, or require old archives to reconstruct a claimed standalone result. Keep the source original unchanged when delivering a versioned download. A local output becomes a delivered artifact only when its actual accessible path/reference is returned.

Return the actual artifact or source changes, a concise account of substantive changes, and consequential remaining uncertainty. Do not create a separate report, changelog, or handoff document by default. Do not claim saving to a Library, repository, account, or live plugin without a successful authorized write and appropriate read-back.
