# Conditional Implementation Patterns

Use this reference only after SKILL.md and the SPEC protocol establish that the subsystem or architectural choice is actually needed. These are conditional design options, not universal defaults or claims that the bundled examples were executed. Existing project conventions and verified external contracts win.

## Contents

- [Architecture style selection](#architecture-style-selection)
- [Authorization model](#authorization-model)
- [Interactive state and result ownership](#interactive-state-and-result-ownership)
- [Library and extension boundaries](#library-and-extension-boundaries)
- [Background jobs and async processing](#background-jobs-and-async-processing)
- [Pipeline progress and recovery](#pipeline-progress-and-recovery)
- [Integrations](#integrations)
- [End-to-end deadlines and admission](#end-to-end-deadlines-and-admission)
- [Observability](#observability)
- [Security implementation patterns](#security-implementation-patterns)
- [Scaling and reliability path](#scaling-and-reliability-path)
- [Durable acceptance and outbox delivery](#durable-acceptance-and-outbox-delivery)
- [Idempotency and concurrency contracts](#idempotency-and-concurrency-contracts)
- [Tenant and identity invariants](#tenant-and-identity-invariants)
- [Migration and compatibility](#migration-and-compatibility)
- [Operational contracts and sizing](#operational-contracts-and-sizing)
- [AI and agent component contracts](#ai-and-agent-component-contracts)

## Architecture style selection

### Modular monolith

Strong fit when a small team needs fast iteration, domain boundaries are still evolving, transactional consistency matters, and one cohesive deployment keeps operational cost low. Keep module ownership and public boundaries explicit so later extraction remains possible.

### Microservices

Use only when independent domain ownership, independent deployment/scaling, or failure isolation is a demonstrated requirement and the organization can own distributed-system costs. Define service contracts, data ownership, cross-service consistency, observability, and failure recovery before selecting it.

### Serverless

Useful for intermittent or event-driven APIs, jobs, file processing, and automation when provider/runtime limits, cold starts, state boundaries, and vendor dependence are acceptable. Verify current provider constraints before committing.

### Event-driven coordination

Useful when one action legitimately fans out to independent asynchronous consumers. Define event identity/schema, ordering assumptions, duplication handling, retries, replay/reconciliation, and eventual-consistency effects. Do not introduce events merely to decouple ordinary in-process calls.

### CQRS

Consider only when read and write models have materially different needs, projections/reporting are complex, or the domain cannot be served cleanly by one CRUD model. Account for projection lag, rebuilds, and extra data paths.

### Event sourcing

Consider when reconstructable history/domain events are primary business records. Audit logging alone is insufficient justification. Define event evolution, correction semantics, projection rebuilds, retention, and operational recovery.

### Multi-tenancy

Use when multiple organizations/workspaces share a platform with distinct ownership or configuration. A shared database/shared schema with an ownership key can be the simplest option when it satisfies isolation requirements; schema- or database-per-tenant needs a concrete isolation/compliance/operational reason. Define ownership and uniqueness constraints from the actual domain rather than adding a tenant key mechanically.

## Authorization model

When roles/permissions are part of the product contract, define them explicitly:

| Role/actor | Resource/action | Allowed scope | Enforcement boundary |
|---|---|---|---|
| <Role> | <Operation> | <Owned/tenant/global subset> | <Backend/service boundary> |

Useful rules when applicable:

- Enforce authorization at the trusted backend/service boundary; UI hiding is not enforcement.
- Use deny-by-default only where the project has an explicit permission model.
- Scope owned resources using the system's real ownership relation.
- Record sensitive administrative actions only when auditability is a requirement.

## Interactive state and result ownership

Use only for a required GUI, web UI, TUI, or other interactive client with mutable input or asynchronous results. Identify separate owners for editable input, the submitted input snapshot, persisted job/result state, and the selected historical result. Details, retry, export, and download must use the intended object's saved data, not silently borrow the current form's values.

Capture the operation identity and relevant input/configuration when work is accepted. Associate completion with that identity and the relevant view/session revision. A late result may update its own job record, but must not overwrite a newer edit or unrelated selection. Define whether navigation merely detaches observation or cancels work, and how the client rediscovers durable unfinished work when applicable; these are different operations.

Trace each user action through the actual binding, handler, service, persisted result, and visible outcome. Specify loading, empty, partial, failure, cancellation, and retry states only where the workflow needs them. Preserve an existing usable result during a failed new attempt unless replacement is explicitly part of the contract. When previews or derived assets exist, keep original/result/preview identity and export semantics explicit. A rendered screen or an enabled button alone is not implementation evidence.

## Library and extension boundaries

When the deliverable is a reusable library or a deterministic core, separate domain contracts and orchestration from externally supplied transport, storage, provider, or runtime implementations. State what the core owns and what the caller must supply. A minimal injected interface is not a working provider integration; an extension point is not the extension's implementation. Keep source or asset references opaque when the contract only authorizes pass-through; do not open, normalize, reorder, or infer content from them.

Expose optional capabilities separately when they are genuinely optional, rather than forcing every backend to implement unrelated identity, caching, streaming, or telemetry methods. Define behavior when the optional capability is absent. Keep policy variants separate when their semantic contracts differ; shared plumbing does not require one ambiguous policy with conditional prose.

Validate caller input and configuration before invoking an external extension. Catch recoverable errors at the boundary that owns recovery; do not turn programming/configuration errors into successful fallback or swallow cancellation/termination without the runtime's explicit contract. Where diagnostics are best-effort, isolate sink failures from the primary result and prohibit re-execution of completed work merely to emit a missing event. Where audit persistence is required, specify that stronger failure contract instead of treating every observer as optional.

## Background jobs and async processing

Common reasons for async work include long-running processing, scheduled work, external calls that need independent retries, notification delivery, report generation, media/AI processing, and synchronization.

| Job | Trigger | Payload/reference | Retry eligibility/bounds | Idempotency/duplicate handling | Terminal failure |
|---|---|---|---|---|---|
| <Job> | <Event/action> | <Stable contract> | <Only safe/recoverable failures> | <Key/effect semantics> | <Persisted state/recovery owner> |

A failed-job table or dead-letter queue is one recovery option, not a default requirement. External timeouts do not prove an operation was not applied; retries of mutations must account for that ambiguity. Long-running work should not block an interactive request unless the product semantics require synchronous completion.

## Pipeline progress and recovery

Use for batch/stream ingestion, incremental processing, synchronization, or replayable projection. Define the source identity, ordering, cursor/watermark meaning, checkpoint owner, and the transaction or ordering relationship between output commits and checkpoint advancement. A checkpoint that moved is not proof that every required record was processed. Account for late arrivals, duplicates, overlap windows, concurrent writers, and the retained source needed for replay.

Inspect the single-record failure path: can one malformed record roll back a whole batch and be read forever, while the process and health endpoint remain alive? Bound retries at the appropriate record or partition, distinguish transient failure from repeatable processor failure, and ensure attempt accounting survives the transaction that is rolled back. Detect lack of progress rather than repeatedly declaring an attempted batch successful.

Quarantine is one option only when the product allows explicit partial processing. Persist the source locator, processor/schema version, failure reason, and retry state before advancing beyond an excluded record; make the completeness gap observable and retained for the supported replay horizon. Record output, exclusions, and checkpoint atomically where feasible, or specify crash reconciliation when they span stores. Replay must account for already-applied effects and define when a corrected processor may retry exclusions. Never silently discard a poison record to turn health green. If skipping violates the contract, stop the affected unit visibly with a concrete recovery owner while allowing independent work only where ordering/consistency permits it.

Define what happens when the source has been pruned, a cursor is invalid, or a processor version cannot consume old state. Retention must support the promised replay/overlap window and any evidence-linked records. A rebuild or version gate needs an executable recovery path and explicit availability semantics, not merely an error message. Keep checkpoints, retry state, and quarantine in the existing owning subsystem rather than inventing a parallel ledger without need.

## Integrations

For a concrete external integration, capture:

- provider/purpose and call direction;
- documented authentication/configuration;
- request/event and response/webhook contract;
- timeout and rate-limit behavior;
- duplicate/out-of-order webhook handling where relevant;
- sandbox/staging/production differences;
- failure state visible to the user/operator;
- reconciliation or fallback path when semantics require one.

Verify current provider details against official documentation; do not infer fields, limits, or supported behavior.

## End-to-end deadlines and admission

For synchronous chains, budget the entire user-visible path: admission and queue wait, child calls, retry backoff, processing, serialization, transport, and return margin. The outer deadline must cover the authorized inner work plus the remaining path; equal independently configured timeouts race at the boundary. Prefer one propagated deadline or one authoritative budget definition with derived limits. A child must not start work that cannot finish within the remaining budget unless the product explicitly supports durable continuation.

Count retries, repairs, and fallbacks inside the same elapsed/cost/call budget. Define bounded admission and backpressure before work enters an unbounded executor or queue; a limit on active workers alone does not bound waiting requests. Specify what the caller observes on rejection, queue expiry, cancellation, and timeout, and whether those events also stop work or only detach the caller.

For durable asynchronous work, request timeout may legitimately precede completion: return or preserve the operation identity, provide a retrieval/resume path, and define how late results remain deliverable without re-running paid or mutating work. An accepted request, a computed result, and a delivered result are different milestones. Do not copy a case study's timeout numbers into a new system without its workload and delivery contract.

## Observability

Choose signals that answer actual operational questions. Common candidates, when relevant, are structured logs with request/job correlation, user or tenant identifiers where appropriate, dependency timing, queue depth, job failures, database latency, and health/readiness checks.

Metric names such as the following are illustrative only and should follow the project's telemetry conventions:

```text
http_request_duration_seconds
http_requests_total
job_failures_total
queue_depth
db_query_duration_seconds
auth_login_failures_total
```

Separate process liveness, readiness to serve, dependency reachability, and successful business/data-flow progress. Measure a useful boundary such as source records observed, records accepted/processed, last successful advancement, excluded records, or delivered results. A zero lag value based only on a moving poll cursor can hide that the consumer is matching no data. Name the signal's source, window, unknown state, and action on violation; do not infer end-to-end success from an HTTP health response alone.

Trace deployment identity, namespace, routing keys, and effective configuration from producer through storage/transport to consumer. One component may own identity while others consume an explicitly derived value; independently maintained defaults and fallback chains need consistency checks. Distinguish expected quiet periods, a newly initialized source, configuration mismatch, and stalled processing. Missing traffic is not always a startup failure: use the expected activity and discovery evidence rather than a universal “must see data” threshold.

Match response to the real operator and recovery model. Preserve the reason behind non-obvious guards when it explains a recurring failure. Do not create a monitoring platform for a system that does not need one.

## Security implementation patterns

Load this subsection only when security requirements are in scope. Select only controls that answer a concrete threat, compliance requirement, or established project baseline. Examples from the earlier kit include backend input validation, parameterized SQL/query binding, managed secret storage, secure session-cookie attributes for cookie-based sessions, rate limiting for exposed abuse-prone endpoints, and approved password hashing for locally managed passwords. Verify algorithm/library/provider recommendations against current authoritative guidance before making them concrete.

Do not turn this catalog into an unsolicited security-improvement backlog.

## Scaling and reliability path

Prefer evidence-driven scaling. For a typical stateful service, a reasonable progression may be: measure the bottleneck, fix query/index/application inefficiency, scale stateless request/worker capacity where appropriate, add read replicas or partitioning only when access patterns justify them, and extract independently scaled services only when ownership or load requires it.

State practical limits and a revisit trigger. A scaling path is not a prediction that every step will be needed.

## Durable acceptance and outbox delivery

Choose a database-resident job or transactional outbox when a committed business change must not lose its asynchronous follow-up. Specify the actual transaction that creates business state and the durable work record together. A later dispatcher or worker processes committed records; never describe a database write followed by a separate broker call as one atomic operation.

A concrete design identifies:

- a stable event/job identity and schema version, its business record, and any immutable payload snapshot;
- eligibility and ordering, atomic claim/lease ownership, bounded work, and what happens when the owner disappears;
- which step records acceptance, attempt, external result, and terminal state;
- duplicate delivery behavior, retry classification, and the recovery path for a crash between external success and local acknowledgment;
- a reconciliation query/process that can rediscover accepted work after queue loss;
- retention of work records and deduplication keys for the actual replay horizon.

Do not promise exactly-once external effects from a unique local key. Separate one committed business mutation, repeated message delivery, and an external provider's documented deduplication guarantee. An unknown external outcome needs provider reconciliation, supported idempotent replay, or an explicit operator decision; a blind retry is not a proof of safety.

The transactional outbox pattern and its duplicate-relay limitation are described by the pattern author in the [transactional outbox reference](https://microservices.io/patterns/data/transactional-outbox.html). Apply the mechanism to the chosen stack; do not infer a provider-specific API from the pattern.

## Idempotency and concurrency contracts

For a retryable mutation, define the key's owner and scope, request fingerprint, retention, and replay response. Reuse of a key with different input must not silently return an unrelated result. Decide how concurrent identical requests serialize and how incomplete attempts become observable. The key and committed mutation must share a consistency boundary or a documented repair path.

For state transitions, define allowed source and target states, expected version/precondition, transaction boundary, and conflict response. Distinguish a missing resource, inaccessible resource, stale version, invalid transition, and temporarily unavailable dependency. Preserve an existing API's error contract.

For cancellation, specify when it is accepted, how workers observe it, and whether an irreversible side effect may already have happened. A canceled UI request is not proof that server-side work stopped. Record partial completion explicitly.

## Tenant and identity invariants

Use the real membership model: one organization per user, multiple memberships, or isolated accounts. Explain how login identifies the correct account if the same email can occur in several tenants. Define invite acceptance, account activation/deactivation, role changes, and the last-owner rule when they are part of the product.

For shared tables, a tenant column alone does not prevent a child from referencing another tenant's parent. Specify the invariant at both the service and storage boundary where applicable, for example composite unique keys and foreign keys. Keep identifiers consistent across DDL, APIs, URLs, jobs, and examples. Define whether timestamps are generated by the application or database and how updates advance them.

PostgreSQL constraint semantics are documented in the [PostgreSQL constraint reference](https://www.postgresql.org/docs/current/ddl-constraints.html). Other databases may enforce different constraints; verify the target engine rather than copying PostgreSQL DDL mechanically.

## Migration and compatibility

For an existing-system change, map observable capabilities to their current and target paths, retaining each capability unless a change or removal is authorized. Identify unresolved gaps, including export, history, cancellation, configuration, failure handling, and other existing paths actually relevant to the change. Define the current and target contracts, all writers/readers, conversion rules, and how mixed versions coexist. Use a dependency-ordered sequence such as expand, deploy compatible writers/readers, backfill, reconcile, cut over, then remove obsolete structures only after dependents are gone. This is a design option, not a universal mandatory rollout.

Cover resumability, checkpoints, concurrent writes, dual-write failure handling if used, data reconciliation, consumer permissions, and external references. Separate rolling back application binaries from reversing a lossy data conversion. Name the last reversible point, the evidence to advance, and the recovery path after that point. Do not equate a backup's existence with a demonstrated restore.

For each phase, identify incoming traffic, the authoritative reader/writer, what prevents or detects divergence, who performs cutover, and the evidence that permits advancing or retiring a compatibility path. New code existing beside old code does not complete the migration. Completion requires the agreed authority switch and consumer convergence; an intentionally retained compatibility window remains explicit remaining transition work, not unexplained permanent duplication. Use the capability and transition tables in `templates.md` only when needed, not a new inventory file.

## Operational contracts and sizing

Define only the operational behavior required for this system: configuration, startup dependencies, health/readiness meaning, graceful shutdown, in-flight work, bounded resource use, and recovery ownership. A healthy process does not establish that its primary workflow or dependency is usable.

For load or cost decisions, state the workload, unit, measurement window, assumptions, and source date. Separate average from peak, latency from throughput, and request acceptance from completed work. Prefer a small explicit capacity/cost model over invented precise forecasts. Scaling triggers must reference an observed bottleneck, not a generic sequence of fashionable technologies.

When a number drives a decision, show the formula, input values and their units, source or assumption for each input, denominator, time window, and rounding. Keep measured, supplied, assumed, and calculated values distinct. Compute using an available calculator/runtime rather than inventing arithmetic results. Preserve precision during calculation and round only the reported result; do not imply more accuracy than the inputs support. Check dimensional consistency, comparable populations/conditions, and whether retries, fan-out, peak load, storage, and other material costs are included. If a decisive input is unknown, use a labeled range or sensitivity scenario when justified, or leave the estimate unresolved instead of inventing a point value. A calculation is a projection, not an observed benchmark.

For data pipelines, also define source cursor/watermark, late and duplicate records, backfill/replay semantics, schema evolution, write atomicity, and how completeness is reconciled. For local tools, define file selection, output naming, overwrite behavior, partial-batch failures, exit behavior, and the path to the actual output instead of adding service infrastructure.

## AI and agent component contracts

Use only when model-driven behavior is part of the product requirements. Prefer an ordinary deterministic function when it satisfies the task; model orchestration, retrieval, memory, and multiple agents are not default subsystems. The following are architecture design choices to adapt, not guarantees supplied by any model or provider.

### Prompt boundary and output

Define one task with its caller, objective, allowed inputs, required context, and observable outcome. Put stable instructions in the instruction layer the host actually supports; keep retrieved/user/tool content in a clearly identified data boundary. Define placeholders once, preserve domain terminology, and state what happens when a required field or source is missing. Delimiters clarify intent; they are not an authorization or security boundary by themselves.

Use the lightest effective prompt: objective, relevant inputs, constraints/priorities, output contract, and failure behavior. Add a persona, examples, extra reasoning stages, or delegation only when they resolve a demonstrated need. Request a concise rationale or evidence where useful, not private chain-of-thought or hidden instructions. Do not embed credentials in prompts or examples.

For a machine consumer, define required fields, types, enums, nullability, units, and IDs/references. Use native schema-constrained output only where current target documentation confirms support; otherwise plan application parsing/validation without claiming the prompt guarantees validity. For a human-facing design response, allow flexible prose rather than imposing a JSON envelope.

The caller owns structural validation and domain checks: referenced objects must exist, cited evidence must be supplied/read, ranges and relationships must be valid, and proposed actions must stay within the authorized scope. Syntactically valid JSON is not proof of correct facts or permissions. Preserve distinct handling for missing information, malformed/truncated output, provider refusal, dependency failure, and an ambiguous external outcome. Define the user-visible result for each relevant case.

### Deterministic transformation boundaries

For a model-assisted rewrite, classification, or optional enhancement, specify the exact terminal outcomes: accepted changed result, legitimate no-op, explicit fallback/degraded result, and failure where applicable. No-op can be success; fallback must not be mislabeled as a successful enhancement. Reusing the original is permitted only when the original satisfies the downstream contract and the product authorizes that recovery. Reject invalid caller input or unresolved required configuration before a paid/backend call; do not hide it as a normal fallback.

Define transformations and validation order. Validate the exact final object/text that will be returned, persisted, or acted upon, including effects of trimming, coercion, enrichment, serialization, and protected-fragment handling. Preserve the original separately where required. A raw response that passes checks can become invalid after post-processing. Allow only explicitly harmless normalization; exact text, ordered source roles, identifiers, and user-selected attributes are not interchangeable representations by default.

State the limit of each guarantee. Deterministic orchestration means the same request, policy/configuration, and supplied backend response yield the same core result; it does not make model inference deterministic. Structural checks and exact-fragment preservation do not prove semantic fidelity or downstream quality. When the contract allows at most one model invocation, repair/fallback guidance must not introduce a hidden second call; deterministic local repair or the declared failure outcome is the limit.

### Tool authority and side effects

List only tools actually supplied by the runtime and define their purpose, input preconditions, permitted action scope, required confirmation under the host/user contract, success evidence, and failure response. Enforce authorization and validate arguments in trusted application code; model output and retrieved instructions cannot grant additional privileges.

Treat model-generated tool requests as proposed operations until the controller validates them. For mutations, carry the accepted operation identity across retries and use the existing idempotency/reconciliation contract. If an operation may already have succeeded, discover its state before retrying; asking the model to regenerate a command is not recovery. Do not describe a canceled generation as proof that its tool effects stopped.

### Bounded execution and repair

Separate a transient provider/read error from invalid input, schema mismatch, missing context, an access limit, budget exhaustion, or a user decision. Set task-appropriate bounds on retries, model/tool calls, output size, elapsed work, and cost where these matter; derive numbers from requirements, measurements, or labeled assumptions. Count repair and fallback work inside the same budget.

Retry only when a new attempt can change the result. Identify the failing field/path and distinguish a mechanical representation error from missing semantic content, an invalid reference, or incompatible prompt/schema versions. Repair only when the original meaning is recoverable under the contract. Do not invent a fact, ID, citation, measurement, or accepted decision to satisfy a schema; do not silently coerce an incompatible value. Missing evidence/context requires retrieval or an explicit unresolved outcome, not fabricated repair. Use null, an empty value, or an unknown status only when the actual schema permits it. A missing required value with no permitted unknown representation fails validation and goes to the controller's failure path rather than becoming a fake valid result.

Supply only the relevant schema, error, and source context to a bounded repair attempt. Revalidate the entire affected object and domain relationships, without re-running completed side effects. Stop repeated identical failures with a clear partial/unavailable result and next resolving action. A fallback that changes quality, privacy, cost, capability, or output semantics must be explicit; never silently substitute another model or provider outside the accepted contract.

### State, retrieval, and stage handoffs

For one model call, an input/output contract may be enough. For a genuinely multi-stage workflow, define each stage's owner, input snapshot, prompt/schema version, produced result, validation, and permitted transitions. Keep durable job state in the application rather than asking the model to remember it. Record pending, partial, complete, failed, and canceled semantics according to the project's state model; do not add a second competing status registry.

Carry exact requirement/object IDs, evidence locators, unresolved conflicts, accepted decisions, and applicable permissions across stage boundaries. Send only context the receiver needs; preserve exact schema/evidence text when its wording matters. Treat stage summaries as navigation/context, not independent evidence. Use revision-aware acceptance so late output from an earlier run cannot overwrite newer accepted state. Recompute only affected downstream results when inputs or contracts change.

For retrieval, specify corpus and access scope, freshness/version policy, evidence locators, and behavior for insufficient or conflicting sources. Retrieved content cannot modify tool permissions or instruction priority. Do not require a vector database, reranker, or claim graph without a retrieval need that justifies it.

### Policy identity and optional caching

When reproducible policy selection matters, identify the selected policy, explicit version/default, relevant schema/configuration, and exact content identity. Keep released versions immutable; changing policy text or the default is an explicit change, not silent selection of a numerically latest version. A content hash identifies bytes, not policy quality or compatibility.

Where caching is actually required, include all output-relevant request, policy/model/configuration/schema, source revision, and access-scope dimensions. Canonicalize structural mapping order without silently normalizing user text or reordering positional assets/roles. An opaque asset ID that can refer to changing content needs a revision or another valid invalidation contract. A fallback implementation/class name with unknown backend settings is not sufficient to promise safe cross-instance cache reuse; bypass caching or resolve the missing identity.

Distinguish a deterministic cache-key extension from real lookup/storage, expiry, eviction, and invalidation. Add only the agreed capability. Cached output still needs current authorization and applicable validation; a cache hit is not a new verification. Reusing a stochastic output is a deliberate cache behavior, not a claim that the provider would regenerate the same result.

### Evaluation and record interchange

When evaluation is an explicitly requested product/research capability, preserve it independently of the no-automated-tests default. Compare against the same inputs and relevant settings, retain baseline/no-op behavior, result status, policy/backend attribution, and any actual measurements separately from human judgments. Do not invent semantic-quality scores from deterministic syntax checks or claim downstream image/product quality from prompt-level metrics.

For export, manual annotation, and reload workflows, distinguish the input-case schema from the exported result-record schema. Define which format round-trips nested fields, findings, Unicode, ordered source references, configuration identity, and human annotations; validate internal consistency on reload. A flattened comparison format is not automatically lossless. Scope this to a real interchange need rather than adding an evaluation repository to every AI component.

### Observable completion

Tie acceptance to the user workflow: valid usable output, preserved constraints, actual authorized effects when applicable, visible failure, and bounded recovery. Observe provider/model and prompt/schema versions, latency, usage/cost basis, failure category, and result destination only where needed for support or reproducibility; avoid logging unnecessary private prompt content.

Compare a prompt change against the same representative input and settings when judging behavior. Separate an instruction-diff risk, a manually observed change, and a measured performance improvement. Do not claim an improvement percentage, repeatability guarantee, or production acceptance without the corresponding observations. Follow SKILL.md's explicit-request rule for automated tests; this pattern does not create an evaluation platform or mandatory suite.


## Automation-friendly CLI contracts

Apply when the product actually exposes a CLI to scripts, people, or agents. Keep the project's existing interface and compatibility rules unless a change is authorized. This is design guidance, not a required runtime, generator, or universal set of flags.

### Inputs, output, and errors

Choose an explicit machine-readable output mode appropriate to the consumer. A JSON object/array suits bounded results; NDJSON can suit streaming records; text remains useful for humans. A structured input payload is useful for complex requests, but a small CLI may be clearer with ordinary arguments. Document real flags and validation rather than assuming every tool uses a particular spelling.

Keep machine-output stdout free of progress/prose. Send human diagnostics to stderr. Define where structured errors appear, their stable codes/fields, and exit status semantics; do not alternate incompatible envelopes without a declared contract. Success with no matches, partial output, invalid input, unavailable dependency, operation failure, and cancellation may require distinct representations. Report partial/unavailable measurements as such, not as zero or success.

Auto-switching format based on TTY is a compatibility choice, not a requirement. Prefer an explicit override that behaves predictably in automation. Document precedence between flags, environment, configuration, and defaults. Do not make a format flag silently change the operation's semantic scope.

### Bounded results and streaming

For large outputs, choose relevant limits, pagination/cursors, filters, field selection, or streaming. Declare defaults, ordering, continuation, and truncation/coverage so a bounded result is not mistaken for the entire dataset. Define failure after partial streaming and broken-pipe behavior. A consumer closing a pipe is not proof that an underlying mutation was canceled.

Schema/discovery commands are useful for dynamic or large interfaces; accurate help and examples can suffice for a small fixed command. Discovery describes implemented behavior, not a substitute for it. Do not add a mandatory schema service or invent guarantees from example output.

### Shared core and headless behavior

Where multiple interfaces already serve the same operations, keep domain validation, business rules, and effects in one shared core; CLI/HTTP/MCP adapters translate transport and presentation. A core library need not become a separate binary or service. Add MCP only for an actual consumer requirement, not merely because a CLI is agent-friendly.

Define input, configuration, and failure behavior for noninteractive execution explicitly. Do not unexpectedly prompt on stdin in headless mode. Interactive confirmation, an explicit authorization option, or a dry-run are product-specific choices governed by the actual operation and host/user contract; neither a mandatory prompt for every mutation nor silent permission escalation is a universal pattern. A dry-run's supported checks and unperformed effects must be explicit.

Use the project's actual validation rules for IDs, paths, values, and combinations; do not impose example-specific constraints as universal API behavior. Keep executable checks in the implementation. A prompt, help text, or a sanitized rendering does not enforce the domain contract.
