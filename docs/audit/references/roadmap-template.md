# Fix Roadmap

This roadmap is a human-readable projection of executable ticket metadata.
Apply triage and `Fix Group` through `triage set`, and dependency edges through
`deps add/remove` before generating it. Group shared-file/shared-cause tickets
for one edit session where dependencies allow; roadmap edits never change the queue.

## Phase 1: Critical Path

**Goal:** Stabilize release blockers and shared foundations.
**Tickets:** {list}
**Effort:** ~{N} hours
**Execution check:** first item should match `python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" next --for resolution` unless a dependency is unresolved.

## Phase 2: Quick Wins

**Goal:** High impact, low effort (`priority >= 15` and `effort <= 2`).
**Tickets:** {list}
**Effort:** ~{N} hours

## Phase 3: Feature Parity

**Goal:** Restore LOST and DEGRADED behavior.
**Tickets:** {list}
**Effort:** ~{N} hours

## Phase 4: Backlog / Deferred

**Goal:** Lower-priority work, accepted risk, or deliberate deferral.
**Tickets:** {list}
**Effort:** ~{N} hours
**Status:** Deferred until explicitly reactivated.
