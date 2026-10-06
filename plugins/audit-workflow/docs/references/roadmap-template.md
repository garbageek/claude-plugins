# Fix Roadmap

This roadmap is a human-readable projection of executable triage metadata. Every listed ticket should already be updated with `python3 /path/to/audit-workflow/scripts/audit.py triage set`, and dependency edges should be updated with `python3 /path/to/audit-workflow/scripts/audit.py deps add` or `audit/triage/dependencies.md`.

## Phase 1: Critical Path

**Goal:** Stabilize release blockers and shared foundations.
**Tickets:** {list}
**Effort:** ~{N} hours
**Execution check:** first item should match `python3 /path/to/audit-workflow/scripts/audit.py next --for resolution` unless a dependency is unresolved.

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
