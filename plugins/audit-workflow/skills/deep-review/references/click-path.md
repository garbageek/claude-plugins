# Click-path analysis

Use for a defined touchpoint, page, or shared-state change. Apply the [deep-review finding contract](../SKILL.md); inspection alone does not authorize browser actions or writes.

## Reconstruct the complete interaction

Establish what the actual label, specification, and calling context promise. Identify all supported activation paths in scope: click/tap, keyboard, form submit, drag-and-drop, or navigation. Do not infer parity because one handler exists.

Before following the interaction, map relevant setters/actions to the fields they read, set, reset, or indirectly invalidate. Include effects, subscriptions, persistence, routing, cache invalidation, and cleanup. Shared state mechanisms depend on the application; no specific framework or store is required.

Trace in execution order:

| Step | Record |
|---|---|
| Initiating interaction | Label, component/location, starting state, user-visible expectation |
| Handler chain | Dispatch, guards, callbacks, return/early-exit behavior, arguments |
| State reads/writes | Values read, writes scheduled/applied, unrelated fields reset, owner |
| Effects and asynchronous work | Scheduling, dependencies, cancellation, request identity, success/failure ordering |
| Reset and cleanup | Navigation, remount, selection changes, finally blocks, stale-response handling |
| Final visible state | Rendered output, pending/disabled state, persisted result, observable error |

Inspect the receiving action's implementation. A harmless-looking selection change can reset another action's state. Distinguish synchronous order, batched updates, and eventual async completion; source order alone does not determine completion order.

## Failure patterns to investigate, not automatic findings

- **Sequential undo:** a later action clears an earlier action's intended state.
- **Async race:** stale completion overwrites newer state, pending flags become inaccurate, or cancellation does not reach the writer.
- **Captured state:** a callback uses an outdated value; inspect actual dependencies and update semantics before claiming staleness.
- **Missing transition:** a handler validates or toggles a flag but never reaches the promised operation.
- **Unreachable action:** a guard excludes a required path; prove the relevant precondition.
- **Effect/cleanup interference:** subscription, remount, navigation, or cleanup reverses a valid operation.
- **Interaction parity loss:** one input method reaches the operation but another previously supported method no longer does.

A reset can be intentional. Confirm the owner, contract, and caller before labeling it a defect. Do not force all UI issues into a state-store diagnosis.

## Evidence labels

Use `source-predicted` for a traced outcome that was not exercised; `runtime-observed` for an actual recorded interaction and its result; `unavailable/unknown` for hidden state, missing code, or inaccessible execution. A browser screenshot shows the visible result, not necessarily the event sequence. Logs and traces need the relevant interaction/instance identity.

For a runtime-capable, authorized check, record starting state, exact action, event/state ordering available from the host, and final visible result. Otherwise provide the source trace and the smallest missing observation. Never fabricate browser execution.

Return one finding per underlying failure, using the common finding shape plus its ordered state trace. For larger scope, inspect shared actions first and then their consumers; sequential execution is sufficient. No fixed page roster, agent fleet, framework prerequisite, or automatic ticket creation is required.
