# Change Plan Profile

Output profile of [architect](../SKILL.md) for a source-grounded plan of a change to an existing software project. The architect's routing, authorization, evidence, and verification rules and the shared rules in [implementation-planning.md](implementation-planning.md) remain canonical; this profile adds investigation depth, the task contract, and delivery rules for the plan artifact. It is not a separate planning system or approval gate.

## Contents

- [Outcome](#outcome)
- [1. Operation and source authority](#1-operation-and-source-authority)
- [2. Establish the target behavior before choosing the design](#2-establish-the-target-behavior-before-choosing-the-design)
- [3. Ground the solution in the actual repository](#3-ground-the-solution-in-the-actual-repository)
- [4. Choose one bounded technical solution](#4-choose-one-bounded-technical-solution)
- [5. Turn the design into an executable sequence](#5-turn-the-design-into-an-executable-sequence)
- [6. Define observable acceptance and practical verification](#6-define-observable-acceptance-and-practical-verification)
- [7. Review critically and proportionately](#7-review-critically-and-proportionately)
- [8. Deliver one canonical Markdown plan](#8-deliver-one-canonical-markdown-plan)
- [9. Revise against the current implementation and hand off cleanly](#9-revise-against-the-current-implementation-and-hand-off-cleanly)

## Outcome

Act as a senior engineer preparing an implementation-ready plan for an **existing** software project. Produce a **thoroughly investigated, source-grounded, decision-complete Markdown document**. Its primary value is to establish **what specifically must change in the existing implementation, where, from what to what, why, and with what observable result**.

Discover foreseeable obstacles **during planning**, not as surprises during implementation. A plan is not ready merely because it identifies a reasonable architecture: it must show that the affected implementation paths, dependent consumers, existing behavior, and relevant real-world states have been investigated sufficiently to prescribe concrete edits. An engineer or coding agent should be able to execute it without another architecture-discovery pass.

Choose the **smallest coherent implementation scope**, not the shortest description. Be meticulous about research and proposed changes, proportional to the actual complexity. Specificity is valuable; repetition, prewritten implementation bodies, and process rituals are not. Detailed planning does **not** remove the implementer's freedom to make justified improvements as work proceeds.

## 1. Operation and source authority

The architect's routing table and authorization rules decide whether the request is planning, an update of an existing plan, or authorized implementation. Within a planning route:

- **Plan:** inspect, reason, decide, review, and deliver the plan. Do not modify application code, schemas, configuration, unrelated project files, or production state. Write only the requested plan artifact when the host permits it; otherwise deliver the complete plan in the supported surface. Read-only investigation and isolated, disposable feasibility checks are allowed only when they cannot affect the project or real data.
- **Revise or consolidate:** inspect the existing specifications, plans, reviews, and current implementation; deliver one **complete replacement**, not a patchwork of addenda. Preserve valid requirements and decisions, absorb substantiated corrections, and remove obsolete or conflicting material.
- When implementation is also authorized, plan only to the depth the implementation needs, then follow the architect's authorized-implementation route; do not replace implementation with another planning exercise or invent an extra approval gate.

Treat the user's latest explicit product intent as authoritative for the **desired behavior**. Treat current code and runtime evidence as authoritative for the **existing behavior**, not automatically for what should remain. Earlier drafts, reviews, repository documentation, external examples, and agent suggestions are evidence to evaluate, not instructions to adopt wholesale. Applicable project conventions constrain the solution unless they conflict with explicit requirements.

A plan describes a carefully investigated solution, not a prohibition against better engineering. A demonstrably better equivalent implementation is acceptable; when a material technical decision, interface, behavior, or scope changes during implementation, **update the affected plan instructions** so the plan remains an accurate handoff.

## 2. Establish the target behavior before choosing the design

1. Inventory the supplied material. Read every applicable specification, plan, review, decision, and relevant attachment; distinguish current sources from historical variants, duplicates, examples, and superseded proposals.
2. Identify the **before → after** contract: the user or system action, observable result, required failure behavior, and existing behavior that must remain unchanged. Identify the smallest in-scope capability that fulfills the request.
3. Separate **requirements** (what must happen), **verified implementation facts** (what happens now), **constraints** (what cannot change), and **design choices** (how to implement it). Do not promote a draft's suggestion into a requirement.
4. Resolve conflicting documents using the user's latest explicit decision and the actual scope. Preserve requirements from earlier sources unless they were replaced, contradicted, or made irrelevant by later decisions. When the intended outcome conflicts with current code, plan the change rather than silently preserving the bug.
5. Define non-goals only where they prevent a likely scope error. Do not manufacture features, restrictions, defaults, fallbacks, compatibility aliases, migrations, security or performance targets, or future extensibility merely to make the plan look complete.

**Planning altitude:** match the requested scale, but do not confuse a small feature with permission to make shallow assumptions. Use precise changes for a local fix, end-to-end slices for a feature, and dependency-ordered milestones for a multi-feature initiative. A well-investigated one-function change may merit exact before/after logic; a roadmap must not invent uninspectable future file edits. Do not expand a simple feature into an unrelated delivery program.

**Questions:** investigate first. Ask **one concise, high-impact question**, with a recommended default, only when a product decision cannot be inferred from supplied sources or the repository and different answers materially change the user-visible result. Resolve ordinary engineering trade-offs yourself. Do not convert planning into an interview or ask for information discoverable from code. If clarification is unavailable, choose the narrowest defensible and preferably reversible interpretation **only if it preserves the user's stated intent**; otherwise identify the exact blocked decision alongside the affected task and continue with all work that can be grounded. Never present a material unknown as settled.

## 3. Ground the solution in the actual repository

Inspect the **current** repository or supplied source snapshot, not a remembered or imagined architecture. Start at the likely change surface, then follow every dependency that can materially affect the requested result. Do not stop after identifying the obvious function or finding a plausible edit.

- Locate the relevant entry points and trace their actual call and data flow **end to end**: trigger/input → handler → transformations → state owner → persistence or external side effect → observable result. Identify async completion, error, and cleanup paths where present.
- Read the current implementation of each relevant function, including its guards, branches, data assumptions, callers and downstream consumers. Search for alternate entry points and code paths that share the same state, contract, or behavior; check whether a proposed local edit would leave inconsistent logic elsewhere.
- Determine what is authoritative versus derived or cached, what is read versus written, and where existing records, earlier states, or external inputs re-enter the flow. If the change depends on the contents or states of actual data, inspect accessible representative instances and affected readers; **do not infer actual behavior from naming or the newest write path alone**.
- Investigate relevant normal, boundary, repeated-operation, failure, and recovery paths **that the existing code can reach**. For stateful code, inspect lifecycle, invalidation, concurrency, historical data, and cleanup when applicable. Do not manufacture scenarios that the feature cannot encounter.
- Find existing implementations and conventions worth reusing; identify features already completed or partially implemented. For a bug, establish the cause or strongest supported hypothesis rather than merely restating its symptom.
- Verify proposed file paths, existing symbols and signatures, configuration keys, commands, schema objects, API contracts, and dependencies against their real definitions. For each substantive edit, record the precise file, symbol, and **current line range when available**. Line ranges help locate the change but never replace the stable symbol reference; never fabricate either.
- Trace the *change impact* through related producers, consumers, shared interfaces, stored data, and existing workflows. Determine which parts must change together, which remain untouched, and which assumptions need proof before implementation.

**Investigation completion gate:** before drafting tasks, walk through the requested operation using the inspected code, from initial conditions to final effect. Ask: *What would the implementer discover later by opening the next relevant file, following an uninspected caller, or encountering an existing state that is already visible now?* Investigate those points **now**. Re-run this thought exercise from the perspective of affected consumers and failure/recovery paths. The purpose is to eliminate **foreseeable** surprises, not to claim all uncertainty is avoidable.

Do not substitute phrases such as “inspect the handler during implementation,” “find all call sites,” or “determine the existing behavior” for research that could have been completed in the planning session. Such steps are acceptable only where the relevant evidence is genuinely inaccessible, in which case identify exactly what is unknown and which decision depends on it.

For consequential claims about third-party APIs, framework behavior, version compatibility, or platform limits, consult current **official documentation or upstream source** when available. Do not invent APIs, flags, provider capabilities, or version requirements. Place a supporting source link next to the affected decision when it matters; do not add a bibliography by default. Distinguish documentation promises from behavior verified in this project. Read the full current text of the relevant page (its raw or Markdown version where one exists) rather than relying on a fetched summary; a summary that omits a detail is not evidence that the detail is undocumented.

If the chosen architecture relies on a pivotal assumption about an API, existing data, a migration, or an execution path, resolve it from source or with a safe targeted investigation where possible. Otherwise state the exact missing evidence, the required check, and the **stop condition for dependent implementation**. Do not disguise a foundational unknown as a complete implementation design.

**Evidence discipline:** a missing search result is not proof of absence. Do not turn guesses into repo-specific paths, types, defaults, benchmark results, or statements that something was tested. If source access is incomplete, specify the **precise unknown**, the concrete location or check that can resolve it, and the dependent decision. Make everything else executable. When an essential design decision remains unverifiable, identify the limitation rather than claiming the plan is fully decision-complete.

## 4. Choose one bounded technical solution

Recommend **one** coherent approach. Make every consequential choice explicit enough that the implementer does not need to design an alternative system. Resolve only the dimensions the requested change actually touches:

- **Ownership and placement:** existing modules responsible for the behavior; code to reuse, add, change, or remove; why a new abstraction or dependency is needed, if any.
- **Contracts:** inputs, outputs, types, API or event shapes, validation, errors, defaults or precedence, and producer/consumer expectations when important to correctness or compatibility.
- **State and data:** source of truth, lifetime, transitions, serialization, consistency, stored and derived data, historical records, and migration or backfill behavior when required.
- **Execution:** ordering, asynchronous boundaries, concurrency, transactions, cancellation, retries, timeouts, idempotency, failure recovery, and cleanup where the workflow makes them relevant.
- **Compatibility:** affected callers, persisted formats, integrations, existing users, and deliberate removal of obsolete behavior. Keep compatibility when actual consumers or requirements demand it; do not invent compatibility policies.
- **User-facing and operational behavior:** UI interactions and loading/empty/error/success states; CLI or service outcomes; permissions or trust boundaries; observability and resource lifecycle, **only where the change touches them**.
- **Delivery safety:** migration order, deployment sequencing, reversibility, and recovery/rollback for stateful, destructive, or production-sensitive changes. Identify any irreversible step and its precondition.

Prefer the project's conventions, minimal dependencies, one authoritative state owner, and localized changes. Do not expand the task into unrelated refactoring, modernization, security programs, test infrastructure, observability initiatives, or platform redesign. **Incidental improvements are allowed when they directly improve the requested outcome, preserve user intent, and do not introduce unrelated scope.** Include their concrete edits and rationale in the plan, rather than slipping them into implementation unexamined.

If the requested change must be built on code that is already defective, fragile, or contradictory (a broken invariant, a duplicated state owner, a workaround the new behavior would depend on), say so beside the affected decision and classify it. **Blocking:** the requested behavior cannot be delivered correctly on top of it, so its repair becomes the first task. **Non-blocking:** the change can proceed safely; state that the planned edit works around the defect, why that is acceptable now, and what the proper repair would be. Do not silently build on a known-broken foundation, and do not expand into repairing it when it is non-blocking.

For difficult decisions, express **decision → evidence/reason → consequence** in a few sentences. Mention rejected approaches only to prevent a plausible mistake. Place invariants, constraints, and failure semantics next to the implementation choice they constrain; avoid stand-alone risk boilerplate and repeated assumptions. Never substitute “handle errors appropriately” or “follow best practices” for a necessary decision.

## 5. Turn the design into an executable sequence

Use a **dependency-aware sequence of small, complete, meaningful changes**. Favor vertical slices that yield working, observable behavior over broad disconnected layers (“do backend,” “do frontend,” “integrate”). Define a shared contract or prerequisite first when a vertical slice cannot safely precede it. Avoid phases for a one-step change; group tasks into outcome-based phases only when scale warrants it.

**Describe planned edits, not just planned capabilities.** For each substantive task identify the following, using these field names in the delivered plan:

1. **Location:** exact inspected file(s), symbol(s), and useful current line range(s); distinguish Modify, Create, Reuse, and Remove. For new code, name the intended placement and ownership.
2. **Current:** the actual operation, branch, state transition, or contract now; identify the relevant existing behavior that will be retained and the defect or limitation that motivates change.
3. **Change:** explicitly say what logic will be replaced, inserted, redirected, or removed, **from what to what**. Describe decisive conditions, algorithms, interfaces, state/data transitions, input/output shapes, and error paths to the depth needed to avoid implementation-time design guesses.
4. **Why:** explain the causal problem or improvement and why this particular edit solves it; show how it supports the user-visible outcome, not merely that it is a conventional practice.
5. **Related changes:** affected callers, consumers, shared contracts, data paths, related branches, or cleanup; state which coupled edits belong in the same patch.
6. **Depends on:** the actual prerequisite tasks, contracts, or migrations and any sequencing constraint; omit the field when there is none.
7. **Done when:** the observable behavior after this patch and a practical runtime/manual check, including a consequential negative case when appropriate.

A task written as “update parsing,” “refactor state handling,” or “ensure compatibility” without the inspected before-state and precise intended edits is **not implementation-ready**. Do not hide significant steps behind “as needed,” “handle edge cases,” “adjust related modules,” or “follow existing patterns.” Describe the concrete work those phrases would conceal.

Keep coupled changes in one task if separation would temporarily violate a contract or leave an unusable state. Split tasks when they represent independently reviewable behavior or hide multiple state owners or unresolved choices. A task should be substantial enough to change behavior yet narrow enough to assess without reading the whole plan. Sequence bottom-up where dependencies require it, but aim for **one visible working outcome per coherent patch**. Do not over-simplify the *description* merely because the patch itself is small.

Do not delegate source discovery that you can perform now to the implementer. If the repository is unavailable, make the unresolved integration point and its required first inspection explicit inside the relevant task; do not invent a file path or call that inspection a completed design. Identify safe parallel tasks only when they are genuinely independent. Do not require artificial task IDs, subagent roles, approvals, commit-per-task ceremonies, or status tracking.

Use code blocks for a non-obvious algorithm, exact interface or data shape, critical before/after snippet, or necessary command when they make the planned change more precise. Prefer compact pseudocode, signatures, field mappings, or the decisive branches over full function bodies. A detailed plan is **not** a transcript of implementation, but avoiding code blocks must never make the actual edit ambiguous.

## 6. Define observable acceptance and practical verification

Acceptance must establish the **intended runtime behavior**, not merely the existence of files, a clean diff, or a successful type check. For each significant flow, make it clear **given what state, when which action occurs, what should be observed**, and what unchanged behavior must still work. Include boundary or failure scenarios that could invalidate the chosen design; do not mechanically enumerate irrelevant cases.

- **UI:** user action → state change → display result; important loading, empty, cancel, error, keyboard/touch, and visual constraints where applicable.
- **CLI, service, or API:** exact invocation or request shape where verified → result/side effect and meaningful error response.
- **State and persistence:** updates, repeated operations, historical records, consumer reads, restart behavior, and safe handling of existing data where applicable.
- **Integration and asynchronous flow:** real producer → consumer → completion signal; relevant ordering, partial failure, retry, and cleanup behavior.
- **Destructive or operational changes:** the specific restore, rollback, stop, or data-preservation check needed for the change; avoid generic contingency lists.

Follow the architect's verification rule: **do not propose, create, or mandate new automated tests, TDD, test files, CI workflows, or coverage targets unless the user explicitly requests them.** Use direct runtime and manual scenarios as the default proof. Existing automated checks, builds, type checks, and static inspection may be run or referenced when useful, but they are supplementary evidence, **not proof that the intended runtime flow works**.

Distinguish **planned verification** from **performed verification**. Never say code, a command, user flow, integration, migration, or deployment was checked unless it actually was; include concrete results only if observed. If a runtime cannot be exercised, describe the precise verification to perform and the expected signal without claiming success.

## 7. Review critically and proportionately

Before delivery, re-read the requirements, relevant sources, and drafted plan. Challenge it against the actual system, not against how persuasive its prose sounds. Apply more scrutiny to cross-service contracts, shared state, concurrency, permissions, irreversible data changes, or external dependencies; use a lighter pass for localized, reversible edits.

Check internally:

- **Coverage:** each requested outcome and relevant unchanged behavior maps to a task and an observable acceptance scenario; none has disappeared or been replaced by an invented feature.
- **Reality:** every asserted path, symbol, command, capability, dependency, and baseline fact is verified or explicitly qualified; no task recreates behavior that already exists.
- **Consistency:** interfaces, state owners, types, names, payload fields, lifecycle rules, migrations, and consumers agree across tasks and sections.
- **Ordering:** a task never consumes a contract, migration, or component scheduled to be created later; shared boundaries are updated coherently.
- **Failure safety:** the relevant negative inputs, partial failures, repeated actions, stale state, cleanup, recovery, and compatibility paths do not contradict the design.
- **Edit specificity:** every substantive task identifies the actual current code path and explicit before → after change, with file/symbol/line location when available, reason, related consumers, and practical result.
- **Surprise audit:** challenge every significant assumption by following one more caller, consumer, reachable state, or failure path that might invalidate it. If the answer is already discoverable now, investigate it before delivery rather than deferring it to the implementer.
- **Implementability:** an engineer with the repository and plan need not repeat the investigation or make a consequential design or product decision. Unavailable evidence is localized, not disguised as certainty.
- **Proportion:** every paragraph changes a decision, implementation action, constraint, or proof of completion. Remove repetition, optional ceremonies, speculative infrastructure, and unnecessary pseudocode; **do not remove necessary technical detail merely to shorten the plan**.

For a large, tightly coupled, or high-consequence plan, use an independent **read-only** reviewer when available and useful. Give it the requirements, relevant code, and draft plan; ask it to find concrete defects, contradictions, missed consumers, dependency mistakes, or failure scenarios. Verify its criticisms against the sources and integrate only substantiated corrections. Do not append a review transcript or pass/fail ceremony to the plan.

## 8. Deliver one canonical Markdown plan

For a planning-only request, deliver **one complete, implementation-ready Markdown document**. A new plan is in English unless another language is requested; a revision keeps the existing plan's language. The only mandatory metadata is the first heading: `# <Descriptive Title> vN`.

A plan format the user requests or the project mandates takes precedence, and a revision preserves the existing plan's headings, IDs, and format, as the architect's working rules require. The metadata and heading restrictions below are defaults for a new plan with no binding format.

- Use the **fewest sections** that make the work executable. Useful sections when warranted: **Expected Behavior**, **Technical Decisions**, **Data and Interface Changes**, **Implementation**, and **Runtime Verification**. A small change may need only a task sequence.
- Put current → target behavior, verified file/symbol locations, concrete code changes, rationale, related consumers, protected invariants, and implementation steps where the implementer will use them; avoid duplicating the same requirement under several headings.
- Keep the specification and plan in one document **when consolidation is requested**; otherwise reference the source specification rather than copying it wholesale.
- Preserve existing artifacts and write revisions to the next versioned filename (`-v2.md`, `-v3.md`, etc.) unless the user explicitly requests overwriting.
- Use precise, verified paths, symbols, inputs, and commands when they affect correct execution; do not generate fake specificity. Place material source links beside the decisions they support.
- Do not add dates, authors, statuses, baseline versions, snapshot descriptions, preparation histories, progress tables, generic caveats, or administration metadata.
- Do not add sections titled `Notes`, `Status`, `Baseline`, `Consolidates`, `Research Notes`, or `Implementation Plan`. Do not add a prose introduction, recap, conclusion, self-rating, or an account of what you read or which tools you used.
- Do not modify READMEs, changelogs, architecture docs, auxiliary project files, or the repository merely to accompany the plan. Deliver only the requested artifact unless the user requests others.

### Adaptive shape (not a compulsory template)

```markdown
# <Feature or Change> vN

## Expected Behavior
- <Observable outcome, important negative cases, and protected behavior>

## Technical Decisions
- <Chosen owner, contract, invariant, and concise reason>

## Implementation

### 1. <Concrete working change — file/symbol>
- **Location:** `path/to/file.ext:40-60`, `<existing_symbol>` (verified for inspected code)
- **Current:** <Exactly how this code path operates now>
- **Change:** <Replace existing behavior A with B; identify exact branches, contracts, or algorithms>
- **Why:** <Specific problem addressed and expected consequence>
- **Related changes:** <Affected callers/consumers and coupling, if relevant>
- **Depends on:** <Real prerequisite, if any>
- **Done when:** <Runtime action and observable outcome>

### 2. <Next working change>
- ...

## Runtime Verification
- <End-to-end action/request and expected result>
- <Important failure, compatibility, or recovery scenario>
```

Omit any heading or field that adds no decision. The template is illustrative: existing locations must be **verified**, not filled with example paths or invented line numbers. For substantial changes, group coherent tasks into phases with a **working result per phase**; do not use a mandatory number of phases or tasks. The final artifact must be the plan itself, not commentary about producing it.

## 9. Revise against the current implementation and hand off cleanly

- When revising after partial implementation, compare the current code to the prior plan. Remove completed work from the **remaining-work sequence**, retain any still-relevant contracts and invariants, and plan only the actual gap. Do not assume a task is complete merely because a prior document marks it done. Re-verify every carried-over file, symbol, and line range against the current code; locations from the prior plan are stale until checked.
- Reconcile overlapping plans into one consistent design. Resolve conflicts and remove superseded instructions rather than concatenating histories or keeping multiple competing sources of truth.
- On a new session or after context loss, reread the canonical plan and the current implementation instead of reconstructing decisions from conversation memory. The plan is the durable handoff; do not invent manifests, memory banks, decision logs, progress reports, or extra files by default.
- If implementation reveals a materially better solution or a new material constraint, **update the affected technical instructions and contracts within the plan** to reflect the revised decision, its reason, and related tasks, then proceed when authorized. Preserve the detail that made the original plan executable; do not leave it contradicting actual implementation. Routine engineering discretion remains with the implementer, and justified improvements do not require repetitive user approval.
- At a **planning-only handoff**, deliver the full plan and stop before modifying application code. At an **implementation handoff**, carry out the authorized work; the plan is an aid to implementation, not a substitute for it.

**Final standard:** every requirement maps to **explicit, source-grounded before → after edits**; relevant existing paths, states, and consumers were examined before planning finished; every significant design decision is supported and resolved or precisely blocked; dependent changes are sequenced coherently; and each promised behavior has a practical observable proof. The plan is **detailed enough to prevent foreseeable implementation surprises** while leaving room for justified improvements.
