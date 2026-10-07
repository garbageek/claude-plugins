---
name: recover
description: Assess and recover an existing project after suspect changes caused regressions, incomplete replacements, authority splits, compatibility loss, or scope drift. Compare trusted baselines and preserve valid improvements. Assessment is read-only by default; execute only an explicitly authorized recovery boundary. Do not use for routine features or normal session resumption.
---

# Project Recovery

Restore the required behavior with the smallest evidence-backed change, not a new architecture or a reflexive return to the oldest version.

Use the [architect's instruction, evidence, authorization, and verification contract](../architect/SKILL.md). Read the [recovery protocol](references/recovery-protocol.md) for this route. It refines recovery, not the authority of the main architect skill. Examples and diagnostic patterns do not create new permissions.

## Select the actual mode

**Assessment — default:** inspect sources and available runtime evidence without changing project files or operational state. Establish trusted baselines, recover the intended contract, compare current behavior, and classify changes as KEEP, RESTORE, SIMPLIFY, COMPLETE, REMOVE, or INVESTIGATE. Return an inline assessment and the smallest justified recovery sequence; write a report only when requested.

**Authorized recovery:** when the user's request already authorizes recovery actions, perform the bounded assessment first and then execute within that authorization. Do not ask for ritual re-approval of already approved work. Preserve useful newer improvements, unrelated changes, user data, and compatibility. A review-only/status turn remains read-only even during ongoing recovery.

Do not automatically create branches, worktrees, archives, checkpoint commits, new tests, or an artifact bundle. Establish an appropriate preservation/rollback strategy from the existing project workflow and the actual operation; separate any additional destructive operation from assessment authority.

## Sequence

1. Contain expansion within the affected scope; do not continue a suspect rewrite merely because it has started.
2. Read actual user requirements and candidate baselines, including their limitations.
3. Compare baseline/current behavior, authority, compatibility, operational burden, and scope.
4. Separate confirmed damage, suspected damage, and improvements worth retaining; classify each relevant change with evidence.
5. Choose the smallest useful restoration or rollback boundary, including what must remain untouched.
6. In authorized recovery mode, restore behavior and missing connections first, then authority and compatibility, then remove proven-redundant paths or simplify within scope.
7. Verify applicable parity gates using permitted existing mechanisms and direct manual/runtime evidence. Report unobserved gates explicitly; syntax or a diff alone is not runtime parity.

Do not classify abstractions, adapters, multiple stores, or newer code as damage without a demonstrated contract/operational consequence. Do not treat old code as authoritative solely because it predates the problem.

## Result and stop rules

Assessment includes trusted baselines, confirmed damage, suspected damage, preserved improvements, rollback boundary, recovery sequence, compatibility risks, and a validation plan. Use the protocol's compact comparison/finding shape; do not generate a second architecture specification.

Use RECOVERY BLOCKER when a particular next action would deepen damage or depends on unresolved critical evidence. State that evidence and continue independent safe work where possible. Use ROLLBACK RECOMMENDED only with a comparison showing why the selected rollback is preferable and what newer improvements survive it.

Recovery completion requires supported behavior/compatibility parity, unambiguous authority for the affected facts, and the applicable operational/documentation consistency gates. Record unavailable execution as unavailable, not passing. Do not reapply the suspect plan wholesale after restoration. Ordinary architectural design and normal session resumption remain with `architect`.
