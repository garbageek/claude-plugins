# Human operation and attempt contract

Use with [human-execution-runbook](../SKILL.md) when the procedure needs decisions, consequential actions, retries, waits, or resumption. Keep the useful contract even in compact output; omit inapplicable fields and ceremonial logs.

## Operations are not attempts or decisions

An **operation** is the intended state change. An **attempt** is one bounded try at that operation. An **observation** supplies evidence about what happened. A **decision** records human judgment from evidence. **Final validation** checks the overall outcome independently.

One numbered step records one bounded attempt. After a terminal result, preserve its action, definition of done, result, decision, and evidence. A retry, rollback, recovery, or repeated classification becomes a new step; never rewrite a failed attempt into a successful one. Use suffix numbering for inserted steps and the next number for appended work. Downstream dependencies point to the successful new attempt, not the historical failure.

An unchanged contract can be explicitly reused by a later attempt; restate changed inputs/revision and routing. Do not reuse it when the required action, acceptance, or failure handling changed.

## State and evidence

| Field | Values and meaning |
|---|---|
| Status | Not started / In progress / Blocked / Completed: lifecycle of this attempt |
| Result | PASS / FAIL / BLOCKED / NOT_APPLICABLE: terminal observed outcome; omitted while nonterminal |
| Decision | Tokens defined for this specific gate, with human decision basis; not a global enum |

Allowed nonterminal states have no Result. `Completed / PASS` means the step's observable definition of done passed. A failed mutation attempt is `Completed / FAIL`. A discovery/classification step that establishes a blocker is `Completed / BLOCKED`. `Completed / NOT_APPLICABLE` retains the original definition of done and names the gate, reason, and replacement dependency path; do not use “Skipped” to erase work.

For a decision gate, a valid recorded decision can be PASS even when the decision is REJECT or ROLL_BACK. Route by **Decision**, not simply by Result. Insufficient evidence to decide is BLOCKED.

Before a step is terminal, append changed status and new observations without silently revising its action. Later contradictory evidence requires a correction note identifying the prior record, new evidence, affected downstream assumptions, and the replanned path. Do not erase the original result.

Use evidence that identifies resulting state: URL/ID/revision, read-back output, observed version, screenshot, approval, or timestamp where known. A click or submitted command alone is not success. Do not invent timestamps or observed facts. Trivial read-only steps need only a meaningful definition of done unless later resumption depends on recorded evidence.

## Step shape

Each necessary step identifies:

- **When:** the satisfied dependency or observable trigger; omit for an immediately startable first step when uninformative.
- **Interface and target:** exact grounded command, UI path, physical location/object, or other surface.
- **Action:** one human-owned operation without hidden implementation planning.
- **Definition of Done:** a binary observable result.
- **Evidence:** only the transition evidence needed by this step or its consumer.
- **If it fails:** one grounded response for each applicable failure class.
- **Next:** the permitted next step/continuation/terminal outcome conditioned on result and decision.

Use status/result/decision fields when execution state is being tracked. Active human time and external waiting are different; include estimates only when useful, label them as estimates, and ground any external deadline/range in the actual procedure. Never invent a time bound to make a wait look complete.

Split steps when they can fail independently, cross authority/system boundaries, require intervening judgment, or have different verification/recovery. Do not split every trivial click. For larger procedures, group only at durable resumable boundaries, never mid-mutation or before required verification.

## Action classes and recovery

| Class | Required handling |
|---|---|
| Setup/read-only | Direct action and observable completion; no dedicated pre-check unless needed by the actual task |
| Reversible low-risk mutation | Bounded action; inline verification is acceptable only when it directly reads back the resulting state |
| Consequential mutation | Dedicated preceding pre-check, grounded authorization/target/payload, immediate separate verification, stop/restore conditions |
| Irreversible mutation | Consequential contract plus explicit irreversible consequence and grounded human decision |
| Classification gate | Record observed facts against PASS/FAIL/BLOCKED criteria; do not recommend a fabricated observed result |
| Decision gate | Define allowed decisions, evidence and consequences; give an evidence-backed recommendation, record the human's actual decision |

For consequential actions, distinguish recording a decision, performing the external approval/mutation, and verifying it was recorded. Do not merge those boundaries into “approved and done.”

A pre-check states how long or under what condition its evidence remains valid (or explicit no decay), and what requires re-checking. For a live/shared target, establish the actual concurrency/quiescence condition relevant to the operation; do not assume no other writer or operator exists.

Identify a grounded recovery path and its validity limit. A restore artifact may become unusable after new writes, expiry, or a migration boundary. Destroying such an artifact is a separate consequential action, not routine cleanup. When no safe recovery exists, a preceding human risk decision must present consequence, stop condition, and supported choices; merely documenting the lack of rollback is not authorization.

A data-changing operation needs at least one semantic outcome check, not only row/file counts or object presence. Re-entry behavior must distinguish an idempotent retry from a non-resumable or classify/cleanup-first attempt. A failed non-resumable attempt cannot simply resume in the middle.

## Failure routing

Include only applicable classes: action unavailable, authorization rejected, operation failed, partial/ambiguous mutation, verification mismatch, observation unavailable, or external work stalled.

Name one exact response per applicable class: stop, bounded retry where safe, remain blocked, reject the approval, request a bounded diagnostic, execute a prepared authorized rollback, or escalate through a grounded owner/interface. “Investigate” alone is not an executable response.

After a partial or ambiguous consequential mutation, stop dependent work and insert a read-only classification step to establish actual state. Do not retry because the response was lost; the operation may have succeeded. Follow an existing failure path when it fits; otherwise replan only the affected unfinished suffix.

## External waits

Record what to observe, whether it is safe to leave, the actual notification/callback/next observation trigger for re-entry, and a grounded upper bound or “no established upper bound.” Define terminal classifications and route from them. Do not imply this assistant is monitoring in the background or require continuous polling when a notification/terminal status is available.

Without a grounded re-entry mechanism, stop at a resolution step instead of writing a passive wait. External work can continue while the human is away only when the actual system does so; a runbook does not provision that behavior.

## Agent handoff and blocked continuation

A handoff specifies the bounded task, actual source inputs, constraints, stop boundary, expected returned result, and acceptance conditions. The human step completes only when that result is returned and accepted, not when the request is sent.

For unknown facts, distinguish agent-discoverable, human-discoverable, and only observable during execution. Prepare derived values yourself. Stop the executable prefix at the resolution step when later commands cannot yet be grounded. After evidence arrives, append executable steps and update only unstarted downstream inputs. Do not regenerate completed history.

## Resume and final validation

On resume, read the existing record and new evidence, preserve terminal attempts, append supported updates/corrections, insert the smallest necessary classification/retry steps, and return the **single next permitted action**. Do not silently change a blocked/in-progress attempt into a different operation.

Final validation is the last numbered classification step in a complete runbook. It independently proves the stated Outcome, includes relevant PASS/FAIL/BLOCKED conditions and durable evidence, and routes failures explicitly. Do not combine it with the last consequential mutation. A deferred runbook keeps this as a non-executable contract until the real interface/check is known.

Add a completion record only for an observed terminal runbook: COMPLETED, ABORTED, ROLLED_BACK, or BLOCKED. Name final evidence, the ending step/decision, known effective revision, and remaining scope. COMPLETED requires final-validation PASS; a document edit or all previous checkboxes is not enough.
