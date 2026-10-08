---
name: human-execution-runbook
description: Draft, update from execution evidence, or resume a sequential runbook of actions a human personally performs. Use for manual approvals, external UI steps, release/deployment procedures, operational observation, physical actions, and interruption/retry handling. Keep human authority, attempts, observations, decisions, and final validation separate. Not an implementation plan or autonomous executor.
---

# Human Execution Runbook

Turn the actual task into the shortest executable human-owned procedure. Resolve agent-discoverable facts and prepare derived commands/messages before handing work to the human. This skill drafts and maintains a document; it does not execute or authorize the human's actions.

## Modes

| Request | Behavior |
|---|---|
| Draft | Create one runbook from grounded facts. For a small procedure, use the compact form below. |
| Update from execution evidence | Append only supported state changes/corrections and the next permitted action; preserve terminal attempt history. |
| Resume after interruption | Reconstruct current state from the existing runbook and actual observations; do not repeat completed actions or silently retry an ambiguous mutation. |

Progress, failure, a decision, or newly resolved facts for an existing runbook select update/resume rather than initial authoring. Return the changed portion and next action unless the user asks for the full synthesized document. Edit an existing file only when requested; no automatic companion artifacts or persistent runtime.

## Grounding and responsibility

Read the actual handoff, prior steps, source documentation, and available status. Ground operational values such as target, revision, environment, URL, interface label, timeout, and restore procedure. Prepare authorable titles/messages/payloads from these facts. Human judgment or authorization belongs in an explicit decision gate.

Do not move agent-owned implementation, investigation, configuration generation, or command preparation into the human's sequence unless explicitly assigned. A human-to-agent handoff covers invocation and acceptance of the result, not every internal agent step.

A blocking fact stops the executable prefix at its smallest resolution step. Put dependent work in an unnumbered **Blocked continuation**: missing fact, blocked work, re-entry evidence, and intended final state. No executable command may contain an unresolved placeholder. An observation-dependent branch can be executable when every branch and response is already grounded.

## Compact form — default for small procedures

Use Outcome, only necessary Prerequisites, a short ordered sequence, and final validation. Add current state, abort conditions, assumptions, or waiting behavior only when they matter. Each action states the exact interface/target, one human action, an observable definition of done, what to do on the applicable failure, and the next permitted step. Avoid click-by-click noise and ceremonial records for trivial reading/setup.

For retries, interrupted work, staged procedures, decisions, external waits, or consequential operations, load [Execution contract](references/execution-contract.md). Its attempt/state model supplies rigor where needed; it does not force a large template onto every procedure. A compact runbook must still preserve the applicable operation and recovery contracts.

## Completion boundary

Distinguish operation, bounded attempt, observation/outcome, human decision, and final validation. A runbook edit does not prove a deployment, approval, message, or physical action occurred. Record state only from supplied or retrieved evidence; do not mark steps complete based on intent.

The last executable validation independently proves the stated outcome, not simply that prior steps are checked off. For a deferred runbook, state an unnumbered final-validation contract until the required interfaces/facts are known. Report COMPLETED, ABORTED, ROLLED_BACK, or BLOCKED only when the execution evidence supports that terminal state.

Do not create a daemon, database, orchestration engine, implementation roadmap, automatic report/index bundle, or autonomous monitoring. Preserve the user's language and existing useful runbook structure. A shortening request is not permission to remove required execution, retry, or decision contracts.

## Final consistency check

For an initial runbook, check the entire executable sequence. For a deferred one, check the executable prefix plus its resolution step, blocked continuation, and final-validation contract. For an update/resume, check changed steps and their downstream dependencies while preserving terminal history; recheck the overall Outcome and final-validation contract when continuation changes.

Confirm that the first action starts from actual current state, every dependency points to established evidence or an explicit observation/decision, blocking unknowns never leak into executable commands, and retries never silently repeat ambiguous mutations. Check applicable pre-check/recovery/verification requirements, durable stage exits, and that final validation proves the Outcome independently. Correct document inconsistencies before delivery; this check does not mark any human action executed or any runtime validation passed.
