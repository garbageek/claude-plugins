# Design Gate

Use only after SKILL.md selects design discussion, an architecture decision, or ADR work. This reference refines that discussion; it does not route SPEC requests or impose a gate on already authorized implementation.

## Outcome

Resolve the decision the user actually asked about. Give a recommended direction, the constraints behind it, the meaningful trade-offs, and any unresolved choice. For a short decision, a concise answer is enough.

A Design Brief captures problem, capabilities, constraints, non-goals, and success signals when product framing is useful. It is not an architecture SPEC. If the user requests a SPEC, use the SPEC route and selected output format in SKILL.md; the default has six sections. Output shapes live in templates.md.

## Scale the discussion

| Situation | Approach |
|---|---|
| One bounded decision with sufficient context | Recommend an approach and explain its main trade-off |
| Several plausible approaches | Compare two or three viable options on the actual constraints, then recommend one |
| Open brainstorming | Clarify the problem, explore useful directions, converge when the user is ready |
| Multiple dependent decisions | Resolve parent constraints first, then work through dependent choices |
| Explicit adversarial review | Challenge assumptions and failure paths with evidence; distinguish risk from confirmed defect |

Do not manufacture weak alternatives just to fill a table. Decompose large work into coherent slices while retaining the user's full objective, dependencies, and eventual deliverable.

## Inspect before asking

Read the relevant conversation, supplied artifact, applicable repository guidance, existing decisions, and the affected interfaces. Use tools actually available in the host. Inspect enough source to understand boundaries and failure behavior; stop expanding the search when it no longer changes the decision.

Follow existing naming, ownership, and deployment conventions unless the proposed change has a concrete reason to alter them. Keep adjacent cleanup scoped to the user's goal.

Ask at most two questions per turn, with one decision axis per question. Prefer a short choice with a recommendation when the alternatives are meaningful. Do not ask the user to choose technical trivia the available evidence resolves. Do not assign invented confidence percentages to interpretations.

## Compare and recommend

Evaluate options using relevant constraints: user workflow, data ownership, consistency, failure recovery, delivery effort, runtime cost, compatibility, and operational responsibility.

Lead with the strongest recommendation. Explain what it buys, what it costs, when the alternative would win, and which new evidence would change the recommendation. Prefer reversible choices under uncertainty. Preserve non-goals.

Apply hard constraints before ranking alternatives, including the option to keep the current design. Use comparable workload, version, units, and cost basis; mark unknown or non-comparable cells instead of inventing scores. For decision-changing evidence gaps or conflicts, load `decision-evidence.md` and use the comparison shape in `templates.md` only when a table makes the decision clearer. A bounded recommendation needs no automatic research phase.

For a consequential recommendation, apply “Challenge the recommended decision” in `decision-evidence.md`: check the condition most likely to invalidate the preferred choice and what observation would change it. Reuse sufficient existing evidence rather than expanding research automatically.

Present technical depth proportional to the decision: affected modules, interface contract, data/control flow, failure behavior, migration and rollout implications, and observable acceptance signals where these determine the choice. Use a diagram directly when it clarifies relationships; no separate permission ritual is needed.

## Decision status and authorization

Distinguish proposed, accepted, and unresolved decisions. Do not treat casual interest as acceptance of a consequential design choice.

A request for discussion or recommendation authorizes that deliverable. Produce the recommendation or brief fully; do not withhold an implementation-ready explanation or handoff behind an approval question.

If the user has only asked to discuss, do not edit application source. If the user has already authorized implementation, carry that authorization forward. Resolve routine choices from context and ask only about consequential ambiguity that prevents correct work; do not require blanket re-approval because a change is non-trivial.

The user's explicit scope governs whether to implement, save a brief, or stop at the decision. Do not create planning artifacts merely because a discussion is long.

## ADR lifecycle

Use one record for one significant decision: a durable boundary, technology/dependency choice, data or deployment contract, expensive-to-reverse commitment, or non-obvious exception. Do not create ADRs for every local edit, or replace a requested SPEC or implementation with one. An explicitly requested small decision record can remain concise; no ceremonial refusal or interview is necessary.

Inspect relevant accepted decisions and the actual project before drafting. Preserve the repository's format, directory, numbering, filenames, and terminology. When a separate ADR file is requested or genuinely necessary and no convention exists, use `docs/adr/` if `docs/` already exists, otherwise `adr/`; allocate an unused number from the actual records. Do not invent an existing sequence, decision maker, approval, or historic date when those facts are unavailable. Label a known recording date separately from an unknown decision date.

Use `Proposed` for an unmade choice and `Accepted` when recording a decision the user or an authorized project decision maker has actually made. Preserve project-specific states such as `Rejected`; use `Deprecated` or `Superseded` when the decision's status warrants it. Permission to recommend is not proof of acceptance, and an accepted decision is not proof of implementation. Routine implementation choices within delegated authority do not require an added approval ceremony.

Capture why the decision is needed now, the binding constraints, realistic alternatives (including retaining the current approach when viable), the chosen option, decisive rationale, and both positive and negative consequences. Include uncertainty and material migration/operational costs without inventing alternatives or generic risk lists. Link supporting sources and related decisions when available. Use the compact shape in [templates](templates.md#architecture-decision), not a second full design document.

For a changed accepted decision, preserve the original rationale and follow the project's supersession convention: the successor links to the old record, and the old record's status links to the successor when both are writable. Do not silently rewrite history to imply the new choice was always accepted. If one record is unavailable or read-only, state the incomplete linkage. This is decision continuity, not permission to create duplicate archives or automatic history files.

## Continuity

When resuming, reconstruct the last accepted decision, outstanding question, existing artifact, and next useful action. Use the project's actual paths rather than fixed harness-specific filenames or commands. Follow the protocol’s “Recovery and change impact” rules for source reconciliation and checkpointing; a design-discussion interlude does not erase earlier completed implementation or its authorization.

Keep short discussions in chat. When a durable artifact is requested or necessary for continuity, update the relevant existing document, or create a concise Design Brief/ADR using the project's conventions. Record only decisions and unresolved context needed to continue; avoid redundant progress logs and migration history.

## Completion

Before delivering, check that the recommended approach satisfies the stated goal, preserves non-goals, accounts for consequential failure behavior, and does not hide unresolved core choices. State one concrete next action when useful. A design conclusion is not evidence of implementation or runtime verification.
