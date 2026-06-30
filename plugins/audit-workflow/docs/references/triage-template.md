# Triage Document Template

Write to `audit/triage/triage-{date}.md`.

```markdown
# Audit Triage

**Date:** {YYYY-MM-DD}
**Source of Truth:** `audit export --json`
**Total Tickets:** {N}

---

## Executive Summary

- **Critical blockers:** {N} tickets must be fixed before release
- **Quick wins:** {N} tickets can be fixed in < 1 hour each
- **Major efforts:** {N} tickets require > 1 day each
- **Recommended first sprint:** {ticket IDs}

---

## Priority Matrix

| Ticket | Category | Severity | Impact | Effort | Priority | P-level | Phase | Decision |
|--------|----------|----------|--------|--------|----------|---------|-------|----------|
| 001    | BUG      | critical | 5      | 2      | 20       | P0      | critical-path | FIX |

Impact must be >= severity minimum unless the downgrade is explicitly justified.

For every row, apply executable metadata:

```bash
audit triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path
```

---

## Recommended Order

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
audit deps add 001 --depends-on 003
audit deps add 007 --depends-on 003
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
audit next --for resolution
```

Expected next ticket: `{ticket-id}` because `{rationale}`.
```
