# Summary Template

Copy this to `{project}/audit/SUMMARY.md` when generating the final report.

```markdown
# Audit Summary

**Date:** {YYYY-MM-DD}
**Project:** `{project_path}`
**Total Tickets:** {N}

---

## Overview

{2-3 sentence summary of audit findings and overall assessment}

---

## By Category

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| BUG      | 0        | 0    | 0      | 0   | 0     |
| DEGRADED | 0        | 0    | 0      | 0   | 0     |
| LOST     | 0        | 0    | 0      | 0   | 0     |
| TODO     | 0        | 0    | 0      | 0   | 0     |
| TEST     | 0        | 0    | 0      | 0   | 0     |
| CONFIG   | 0        | 0    | 0      | 0   | 0     |
| SECURITY | 0        | 0    | 0      | 0   | 0     |
| CODE-QUALITY | 0    | 0    | 0      | 0   | 0     |
| **Total**| 0        | 0    | 0      | 0   | 0     |

---

## By Module

<!-- Populate from actual project structure -->
| Module | Tickets | Critical | High | Medium | Low |
|--------|---------|----------|------|--------|-----|
| ...    | 0       | 0        | 0    | 0      | 0   |

---

## Verification Status

| Status | Count |
|--------|-------|
| OPEN   | 0     |
| READY_FOR_VERIFICATION | 0 |
| PASS   | 0     |
| PARTIAL| 0     |
| FAIL   | 0     |
| REGRESS| 0     |
| BLOCKED| 0     |
| WONTFIX| 0     |
| INVALID| 0     |

---

## Critical & High Priority Findings

### Critical Issues

1. **{Ticket title}** ({ticket number})
   - {Brief description}
   - Impact: {what breaks if not fixed}

### High Priority Issues

1. **{Ticket title}** ({ticket number})
   - {Brief description}

---

## Top Recommendations

1. **{Action item 1}**
   - Related tickets: {list}
   - Estimated effort: {low/medium/high}

---

## Next Steps

1. [ ] Review critical tickets immediately
2. [ ] Triage high priority tickets
3. [ ] {Project-specific follow-ups}
```
