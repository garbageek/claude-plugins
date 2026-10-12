# Triage Document Template

Write to `audit/triage/triage-{date}.md`.

Write all decisions, scores, dependencies, and fix groups to tickets through the
CLI *before* generating this document from `export --json`. The report is a
snapshot for humans, not an input to `next`, `export`, or `doctor`.

````markdown
# Audit Triage

**Date:** {YYYY-MM-DD}
**Source of Truth:** `python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" export --json`
**Total Tickets:** {N}

---

## Executive Summary

- **Critical blockers:** {N} tickets must be fixed before release
- **Quick wins:** {N} tickets can be fixed in < 1 hour each
- **Major efforts:** {N} tickets require > 1 day each
- **Recommended first sprint:** {ticket IDs}

---

## Priority Matrix

| Ticket | Category | Severity | Module | Impact | Effort | Priority | P-level | Phase | Decision | Fix Group |
|--------|----------|----------|--------|--------|--------|----------|---------|-------|----------|-----------|
| 001 | BUG | critical | src/parser.py | 5 | 2 | 20 | P0 | critical-path | FIX | parser |

Choose Impact from the actual user/data/release effect and explain non-obvious priority decisions. There is no separate runtime severity-to-Impact conversion.

For every row, apply executable metadata:

```bash
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path --fix-group parser
```

---

## Recommended Order

Group tickets touching the same files or shared root cause into one edit
session when compatible with priority and dependencies. Set a shared `Fix Group`
on each grouped ticket; use separate groups for unrelated edits even if they
share a module. `next --for resolution --json` reports eligible related tickets.

### Phase 1: Critical Path
Must fix before release.

| # | Ticket | Summary | Effort | Rationale |
|---|--------|---------|--------|-----------|

### Phase 2: Quick Wins
High impact, low effort.

| # | Ticket | Summary | Effort | Rationale |
|---|--------|---------|--------|-----------|

### Phase 3: Feature Parity
Restore lost/degraded functionality.

| # | Ticket | Summary | Effort | Rationale |
|---|--------|---------|--------|-----------|

### Phase 4: Backlog / Deferred

| # | Ticket | Summary | Effort | Rationale |
|---|--------|---------|--------|-----------|

---

## Dependencies

```text
# format: <blocking-ticket> blocks <blocked-ticket>
003 blocks 001
003 blocks 007
```

Equivalent CLI updates:

```bash
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" deps add 001 --depends-on 003
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" deps add 007 --depends-on 003
```

---

## Module Groupings

### {module}/ ({N} tickets)

- {ticket list}
- **Fix order:** {sequence}

---

## Effort Estimates

| Effort Level | Tickets | Total Hours |
|--------------|---------|-------------|
| 1 (< 1h)     |         |             |
| 2 (1-4h)     |         |             |
| 3 (4-8h)     |         |             |
| 4 (1-3d)     |         |             |
| 5 (> 3d)     |         |             |

**Total estimated effort:** ~{N} hours

---

## Skip / Defer / WONTFIX

| Ticket | Decision | Reason |
|--------|----------|--------|

---

## Execution Check

```bash
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" next --for resolution
```

Expected next ticket: `{ticket-id}` because `{rationale}`.
````
