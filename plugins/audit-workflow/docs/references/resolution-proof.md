# Resolution and independent verification proof

This guide refines the existing [audit contract](../CONTRACT.md). It does not change actors, states, categories, acceptance gates, or the canonical export. Resolution stops at READY_FOR_VERIFICATION; only independent verification assigns its supported verdict through the existing runtime.

## Separate the three claims

| Layer | Meaning | Record |
|---|---|---|
| Proposed check | What could establish an acceptance criterion | Criterion ID, input/precondition, operation, expected observable outcome |
| Observed result | What was actually examined or executed | Revision/instance, command or source path, environment, actual output, limitation |
| Verdict | What that observation supports | Per-criterion result under the original acceptance criteria; remaining gaps |

A proposed command is not a performed check. An attempted check is not necessarily successful. Source inspection, syntax/schema validation, runtime reproduction, and user/operational acceptance are different evidence. Never promote one into another.

Choose checks from the user's requested scope and the actual project contract. Manual/runtime evidence and existing authorized checks can be appropriate; do not introduce mandatory test generation, suites, or document packs. Do not fabricate missing criteria. A passing aggregate or a suggested verification recipe cannot replace explicit passing evidence for every required criterion.

## Category-specific proof questions

| Existing category | Useful proof, selected for the actual criterion |
|---|---|
| BUG | Show the concrete failing path and the corrected result; inspect adjacent behavior. A before/after reproducer or an authorized existing check may establish it. |
| DEGRADED | Compare the same behavior or metric under comparable inputs/environment; explain any accepted intentional difference. |
| LOST | Demonstrate restored capability and relevant interaction/interface parity, not merely the existence of a function. |
| TODO | Exercise the completed contract, including relevant unimplemented/early-return branches; removing a marker is not implementation. |
| TEST | Explain the contract/assertion gap and what the existing or explicitly requested changed test actually rejects. Claim execution only if performed. |
| CONFIG | Check both syntax/shape and which effective configuration the relevant consumer loaded. Update examples only when needed for the requested correction. |
| SECURITY | For a ticket already in scope, establish the stated boundary behavior using an authorized, bounded reproducer; do not broaden the task. |
| CODE-QUALITY | Show the specific responsibility/maintenance improvement and preservation of observable behavior. Static signals alone do not prove runtime parity. |

These are proof choices, not extra acceptance criteria. Retain the ticket's agreed scope and any project-required evidence.

## Is the corrected code active?

When the claim concerns a running application:

1. Identify the relevant service/process/build/instance and actual activation mechanism: deployment, restart, hot reload, module reload, worker replacement, or another project mechanism.
2. Read the available revision, artifact digest/build ID, module location, instance ID, start time, or reload signal. Establish which signal relates to the changed code and to the instance receiving the request.
3. Distinguish source on disk from loaded code. Look for stale workers, separate scheduled processes, duplicate instances, cached outputs, or a request reaching a different deployment **when evidence makes them relevant**.
4. After an authorized activation, observe the reported behavior again against that instance. Correlate request/event timing; an old queued result does not necessarily describe the new code.
5. State what remains unknown when instance/revision visibility or deployment access is unavailable. Do not claim operational completion from a file diff alone.

A changed PID is neither universally required nor sufficient. Hot reload can correctly preserve a PID; a new process can still run an old artifact. Bytecode-write settings do not reload an already imported module. Deleting state or caches is not a generic prerequisite for proof.

Diagnosis remains read-only unless runtime actions are authorized. Do not restart services, connect to unspecified machines, clear state, create commits, or initiate deployment automatically from this guide.

## Recording and handoff

Resolution records changed files/revision, proposed checks, actual observations, and unresolved activation needs using the existing CLI/MCP resolution fields. Verification independently re-reads the original ticket and relevant current state, maps each acceptance criterion to evidence, and uses the runtime's supported statuses. Use PARTIAL/FAIL/BLOCKED as supported by the contract when the evidence does not justify PASS; do not invent a new lifecycle.

Use canonical export for reporting. Never introduce private CLI bootstrapping or a Markdown fallback parser that reinterprets lifecycle state.
