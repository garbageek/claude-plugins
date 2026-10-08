# Decision Evidence and Targeted Research

Use only for decision-relevant uncertainty in the route already selected by SKILL.md. This reference refines how evidence is gathered and used; it does not impose a research report, separate state store, multi-agent pipeline, or approval gate. Use inline citations and a short rationale when they suffice. Reusable record shapes live in `templates.md`.

## Contents

- [Bound the question](#bound-the-question)
- [Read the right evidence](#read-the-right-evidence)
- [Verify the exact claim](#verify-the-exact-claim)
- [Challenge the recommended decision](#challenge-the-recommended-decision)
- [Compare on an equal basis](#compare-on-an-equal-basis)
- [Repair the smallest gap](#repair-the-smallest-gap)
- [Stop and deliver](#stop-and-deliver)

## Bound the question

State the decision or requirement affected, the unknown that could change it, the relevant system/version/environment, and what evidence would resolve the unknown. Reuse supplied scope, source permissions, budget, and exclusions. Do not ask the user to supply a research plan or invent a mandatory budget field.

Rank unknowns by consequences: correctness of a Must Have, feasibility, compatibility or data loss before low-impact preferences. Inspect supplied code, schemas, accepted decisions, and actual observations first when the question concerns this project. Search outside it only for information those sources cannot establish or whose current external contract needs verification. Explicit user research requests still govern the requested coverage.

Use the smallest useful cycle: identify a gap, retrieve/read the source that could settle it, check the claim, and return to the selected deliverable. Expand only when the result exposes a material unresolved dependency. Do not exhaust a topic or a prompt catalog just because it is available.

## Read the right evidence

Choose sources by the question, not by a universal ranking:

| Question | Appropriate evidence | What it does not establish |
|---|---|---|
| What must this project deliver? | Explicit user requirements and accepted project decisions | That the current code already does it |
| What is implemented? | Exact source revision, entrypoints, callers, configuration and persistence paths | Successful execution or deployment |
| What happened in a run? | Actual operation, environment/version, input, result and relevant logs/state | A universal provider guarantee or another environment's result |
| What does an external product support? | Official docs, schema, source or release notes for the actual target version; current lifecycle/limits where relevant | That a proposed integration is wired locally or an upgrade is authorized |
| Which option fits this workload? | Comparable contracts and applicable measurements, plus explicit project priorities | A universal winner |

Search snippets and titles are leads, not sufficient support for a decisive API, numeric, compatibility, or absence claim. Read the underlying passage, schema, code path, table, or observed result. Inspect a relevant figure or table directly when extracted text loses its meaning. A failed read, partial extraction, or empty search is an access/coverage limitation, not proof that a capability does not exist.

Keep the source locator and version/date/environment when they change the meaning. Deduplicate mirrors and summaries of the same origin; repeated reports are not independent corroboration. Prefer primary evidence for technical claims. Do not upload private source, secrets, identifiers, or internal excerpts to a public search/provider; formulate a generic technical query or use an authorized private source.

A supplied review, prompt catalog, example, or corpus-derived convention is evidence about that material, not automatic proof of the current upstream implementation or an official product rule. Preserve its stated scope, provenance, and limitations. Use extracted patterns as explicit design choices; verify a linked primary source only when the decision actually depends on its present behavior. A frequency observed in one corpus does not establish universal required files, supported enum values, or incompatibility of unobserved variants. A case-study failure mechanism can guide inspection without turning its project-specific thresholds or claimed severity into defaults for another system.

## Verify the exact claim

Split compound claims when their parts need different support. Check the actor, operation, conditions, dates, versions, units, limits, failure semantics, and qualifiers actually asserted. A citation about successful requests does not prove behavior after a timeout. An implemented retry loop does not prove safe replay.

Keep evidence distinct from interpretation: a source passage may **support**, **oppose**, or **qualify** a claim, or provide **context only**. State a recommendation as a design judgment grounded in that evidence and the project's constraints, not as another quoted fact.

| Evidence status | Meaning and permitted use |
|---|---|
| Supported | The inspected evidence supports the claim at its stated scope. This is not an automatic runtime-readiness claim. |
| Qualified | A narrower or conditional claim is supported; include the restriction where the claim is used. |
| Unverified | Sufficient evidence is unavailable or unread; present an assumption/open dependency, not a fact. |
| Contradicted | Relevant evidence conflicts with the claim; expose the conflict and repair the affected decision. |
| Stale | Evidence does not establish the required version/date; refresh it or limit the claim to the known context. |

These labels are working aids, not a required JSON protocol. Explain confidence through evidence strength and limitations rather than invented percentages. Keep a decisive uncertainty in the recommendation and summary, not only in a footnote or appendix. Do not use an earlier generated draft or compressed summary as independent verification of itself.

For conflicting sources, check version/time, environment, definitions, units, methodology, and implemented-versus-promised behavior before declaring a factual contradiction. For a genuine unresolved conflict, retain both supported positions, name the affected choice, and state what observation would resolve it. Neither newer-looking filenames nor confident wording settle precedence.

## Challenge the recommended decision

For a consequential choice, identify the strongest plausible failure of the preferred approach: a hard requirement it might violate, an unproven dependency guarantee, or a workload/operating condition that would make the alternative preferable. State the evidence that would change the decision, then inspect the relevant source, failure path, or measurement when accessible. Reuse evidence already read; this is not a second research phase.

Check that the proposed response to failure preserves the requirement. For example, retrying a timed-out mutation is not an answer to an unknown external effect unless replay/reconciliation semantics are established. A favorable average score cannot repair a failed Must.

If contrary evidence changes the choice, update the recommendation and dependent contracts. If it does not, retain the bounded recommendation with its actual limitations. Do not invent opposition, weaken a supported conclusion for balance, reopen unrelated accepted decisions, or perform this exercise for routine mechanical edits.

## Compare on an equal basis

Apply hard requirements first: an option that fails a Must cannot win because of an attractive average score. Select only decision-changing dimensions, such as compatibility, failure/recovery behavior, delivery effort, operational ownership, latency, and cost. Use the same workload, units, region/tier/version, and measurement basis where relevant.

Mark missing, stale, contested, and non-comparable cells explicitly; never infer a missing capability from a neighboring cell. For cost, distinguish measured usage from projections and show assumptions for input/output volume, retries, storage, network or other material charges. Use the reproducible calculation rules in “Operational contracts and sizing” in `implementation-patterns.md` when a numerical result drives the choice. For performance, separate peak from sustained throughput and submission latency from completed work.

Compare the strongest viable alternatives, including keeping the existing design when it remains feasible. Recommend one, explain its main cost and the condition under which another would win. Rankings or weights must come from explicit priorities or be labeled as proposed; do not fabricate precision. An analogy can justify borrowing a workflow without proving the analogous product's private architecture or importing its entire scope.

## Repair the smallest gap

For each consequential gap identify the affected claim/contract, impact, smallest action, expected resolving evidence, and fallback. Keep this in the current work record; no repair-plan file is required.

| Gap | Smallest useful action |
|---|---|
| Missing decisive passage or partial extraction | Read the exact section, schema, code path, or table; do not restart broad research |
| Unknown or stale external contract | Check official docs/source for the pinned/deployed version and relevant current constraints; keep the integration unverified if unavailable |
| Unsupported part of a compound claim | Split the claim; verify the missing part or retain it as an explicit assumption |
| Contradiction or non-comparable numbers | Align scope/units/versions; inspect both primary sources; preserve any remaining conflict |
| Missing requirement or design boundary | Infer only routine choices within scope; ask a consequential question only when necessary for correctness |
| Missing implementation/wiring | In implementation mode, change the actual source; in review mode, name the exact correction without editing |
| Missing runtime or operator access | Finish independent code/design work; give the exact remaining operation and expected evidence |
| Unavailable or repeatedly failing tool | Change query/path only for a reason, try an available equivalent source, or expose the bounded limitation |

Retry a read only when the cause is plausibly transient or the input/query has been corrected. Repeating the same failed search does not improve evidence. Never replay an external mutation after an ambiguous outcome without first establishing its safe retry/reconciliation contract. Preserve the original requirement when narrowing an unsupported claim; claim repair is not permission to silently lower scope or quality.

## Stop and deliver

Stop expanding research when the decision's critical facts are sufficiently supported at the required scope and no unresolved contradiction can change the recommendation. Also stop an unproductive line when access is unavailable, the user's budget is exhausted, or another search would only repeat the same origin; disclose the resulting uncertainty rather than claim exhaustive coverage.

Before delivery, check the load-bearing claims against the actual evidence and recheck all changed dependent contracts. Keep non-blocking warnings separate from blockers and name the exact blocked task or operational step. An accepted risk is not a passed verification. Do not average a release-blocking defect into a positive quality score.

Return the requested recommendation, SPEC, review, updated artifact, or implemented source. Embed only the evidence detail needed to understand it. Do not replace useful partial work with a refusal, or a requested implementation with a new research plan. Use the readiness levels in `spec-operating-protocol.md` for completion claims.
