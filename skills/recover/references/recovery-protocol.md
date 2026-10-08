# Evidence-based recovery protocol

Apply this reference only through [recover](../SKILL.md). The [architect contract](../../architect/SKILL.md) owns authorization, evidence distinctions, artifact scope, and verification policy.

## 1. Contain without creating more state

Identify the suspect change range and affected behavior before continuing feature expansion, cleanup, or migration there. Do not freeze unrelated work or mutate a project merely because assessment has begun. Read the working tree and user changes; preserve unrelated or uncommitted improvements rather than treating a dirty tree as disposable.

In assessment mode, preserve current state by not changing it. Before an authorized risky operation, identify the actual restore path and limits. Existing revisions, user-provided archives, or the project's normal workflow may be sufficient. Additional archives/branches/worktrees/commits are not mandatory outputs and are not authorized by this reference alone. A code rollback cannot automatically undo data mutations or external side effects.

## 2. Reconstruct the contract and baselines

Read the actual requirements, approved scope, prior behavior, public interfaces, and compatibility promises. Candidate baselines include supplied versions, working releases/tags/commits, source archives, observed workflows, and existing project records. Record which evidence makes each baseline trustworthy **for the affected behavior**. One reference may establish an API while another establishes UI interaction parity.

Distinguish observed runtime behavior from source-predicted behavior, documented intent, and user-reported symptoms. Do not invent a last-known-good revision. Conflicting sources remain visible. The newest design is not automatically authority; the older implementation is not automatically correct either.

Use this comparison inline or in the requested existing artifact:

| Area/contract | Trusted behavior and evidence | Current behavior and evidence | Intentional difference? | Classification / unknown |
|---|---|---|---|---|

Cover only relevant areas: feature/workflow, state authority/read-write paths, API/ID/data/config compatibility, operational steps, and approved scope. For a UI migration, include actual interactions, inputs, navigation, saved state, and results—not only visual resemblance.

## 3. Investigate damage by consequence

- **Functional regression:** a missing feature, bypassed path, incorrect output, ignored configuration, failed workflow, or incomplete generated result.
- **Scope reduction/expansion:** required behavior silently removed or speculative machinery made mandatory without accepted need.
- **Authority split:** competing writers or formats disagree, a projection is mistaken for authority, or runtime and documentation specify different active contracts.
- **Incomplete replacement:** callers still use the old path, an adapter is bypassed, parameters/context do not reach the new implementation, or controls expose ignored settings.
- **Abstraction/operational burden:** extra layers introduce a concrete failure or unnecessary operating dependency, obscure diagnosis, weaken resume behavior, or mutate original input unexpectedly.
- **Documentation drift:** aspirational work marked implemented, incompatible designs both called current, or examples contradicted by the executing path.

These are search lenses. Coexisting stores can be deliberate projections; adapters can preserve compatibility; a verifier may intentionally be read-only. Establish the contract and consumer before treating any pattern as damage.

## 4. Classify each relevant change

| Classification | Evidence needed and action boundary |
|---|---|
| KEEP | Useful working change that preserves the required contract; keep it through recovery. |
| RESTORE | Required earlier behavior was lost/broken; restore that behavior, not necessarily every old implementation detail. |
| SIMPLIFY | Useful new behavior has demonstrated unnecessary structure/burden; simplify only after preserving behavior. |
| COMPLETE | The accepted direction is justified, but a specific integration/migration gap prevents it from working. |
| REMOVE | The change causes demonstrated harm or has no required consumer/value; verify reachability/dependencies before removal. |
| INVESTIGATE | Evidence is insufficient or conflicting; identify the missing observation and do not guess a destructive action. |

For confirmed damage state severity/impact, affected behavior, responsible change or unknown range, trigger/path, exact evidence, and classification. Keep suspicions in a separate group. Classifications are not execution commands.

## 5. Select the recovery boundary

Prefer, where sufficient:

1. reconnect an existing bypassed path;
2. restore missing input/context or parameters;
3. restore a required deletion or compatibility adapter;
4. complete an accepted migration's narrow integration gap;
5. remove proven redundant structure after parity;
6. revert the affected subsystem;
7. revert the full suspect range only when the smaller alternatives cannot restore the required contracts safely.

Compare incremental repair with partial/full rollback using concrete parity, authority, compatibility, data-state, and operational consequences. Do not choose based on line count, novelty, sunk effort, or the number of reported smells. State what each option retains, loses, and cannot reverse. Preserve independently valid improvements introduced after the baseline.

Full rollback is a recommendation requiring its appropriate authorization; a read-only diagnosis cannot execute it. A reset of a code revision does not prove deployment rollback or data compatibility. Avoid redesign during recovery unless the existing options genuinely cannot satisfy the contract and that redesign is within explicit scope.

## 6. Required assessment content, not a mandatory new file

Provide these topics in the user's chosen structure; the default headings are:

- Trusted Baselines
- Confirmed Damage
- Suspected Damage
- Preserved Improvements
- Rollback Boundary
- Recovery Sequence
- Compatibility Risks
- Validation Plan

The sequence specifies exact actions/targets, dependencies, permitted changes, what remains untouched, expected outcomes, and stopping/restore conditions where relevant. Preserve requirement/decision IDs from the canonical project record. Do not create a separate SPEC, milestone set, inventory, or progress ledger just for recovery.

## 7. Execute only within authorization

Restore user-visible behavior before aesthetic cleanup. Trace active reads/writes and migrations before removing competing authority. Preserve stable IDs, old data readability, API/CLI contracts, configuration, filenames/paths where public, and integrations unless an explicit accepted change says otherwise.

Remove an incomplete parallel implementation only after its required capabilities and consumers are accounted for. Complete only justified improvements; do not “finish the platform” to avoid acknowledging an unjustified replacement. Keep changes reviewable without imposing a commit-per-step policy or committing automatically.

Use actual known commands, interfaces, and project mechanisms. Proposed commands remain proposed until run. If a required runtime action is unavailable, deliver supported source restoration and state the remaining activation/observation boundary accurately.

## 8. Applicable verification gates

| Gate | Evidence supporting completion |
|---|---|
| Behavior parity | Required baseline capabilities/workflows operate, or an explicitly accepted change explains the difference. |
| Compatibility parity | Required IDs, interfaces, formats, configuration, stored data, and migration paths still satisfy the selected contract. |
| Authority integrity | Each affected fact has a defined authority; derived views and transition writers are unambiguous and match runtime. |
| Operational simplicity | No unintended additional operating burden remains within the recovery scope; startup/resume/diagnosis work as required. |
| Regression confidence | Concrete confirmed damage paths and relevant adjacent behavior are checked with authorized existing checks or direct manual/runtime evidence. |
| Documentation consistency | Existing canonical instructions/examples match implemented behavior; update only affected documentation when needed. |
| Restore boundary | The stated rollback/continuation path is still valid for the current code/data/deployment state, or its limits are explicit. |

Do not propose, plan, write, or run new automated tests by default. Follow the architect's explicit-request verification rule. A passing syntax check is structural evidence only. A gate requiring unavailable runtime evidence remains unverified; do not claim recovery complete by counting edited files. Not-applicable gates need a short reason, not invented measurements.

## 9. Incident signals and completion

**RECOVERY BLOCKER:** identify observed damage, unresolved evidence, the affected next action, why continuing that action would deepen damage, and the smallest resolving observation/containment. Continue unrelated authorized work when safe.

**ROLLBACK RECOMMENDED:** identify the trusted baseline, suspect range, lost parity, comparative reason incremental repair is riskier, smallest rollback boundary, and newer improvements retained separately.

After recovery, report the actual changes, observed results, remaining unknowns, and next permitted action. Useful newer improvements may be reconsidered individually; never restart the failed plan wholesale. Do not call a source change deployed or a plan executed without the corresponding evidence.
