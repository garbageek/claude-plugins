# Progress Template

Copy this to `{project}/audit/progress.md` when running a systematic audit that covers ≥ 5 modules or is expected to take > 2 hours. This is mechanical coverage tracking, not fix planning. Fix planning is owned by `audit-triage`.

```markdown
# Audit Progress

**Project:** {project_path}
**Started:** {YYYY-MM-DD}
**Status:** 🔄 In Progress

## Modules

<!-- Discover actual modules from the project structure, then list them here. -->
<!-- Example: find . -maxdepth 2 -type d | grep -v __pycache__ | grep -v .git | sort -->

| Module | Status | Tickets | Notes |
|--------|--------|---------|-------|
| ... | ⏳ | - | |

**Status legend:** ⏳ pending | 🔄 in progress | ✅ done | ⏭️ skipped

## Cross-Cutting Concerns

| Check | Status | Issues Found |
|-------|--------|--------------|
| Contract consistency | ⏳ | |
| Error propagation | ⏳ | |
| Concurrency safety | ⏳ | |
| Dependency direction | ⏳ | |
| Test coverage | ⏳ | |
```

---

## Updating Progress

After completing each module:
1. Change status from ⏳ to ✅
2. Fill in ticket count
3. Add any relevant notes
