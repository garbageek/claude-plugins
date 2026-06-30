# Ticket Template

```markdown
# {Brief problem title}

**Category:** `BUG` | `DEGRADED` | `LOST` | `TODO` | `TEST` | `CONFIG` | `SECURITY` | `CODE-QUALITY`
**Severity:** `critical` | `high` | `medium` | `low`
**Module:** `{path/to/file.py}`
**Lines:** `{start}-{end}` or `N/A`
**Source:** `{log analysis | code review | runtime trace | comparison with X | incident investigation}`
**Depends On:** `none` or `003, 007`
**Blocks:** `none` or `012`
**Impact:** ``
**Effort:** ``
**Priority:** ``
**P-level:** ``
**Decision:** `FIX`
**Phase:** ``

## Description

{What exactly is wrong. Be specific and factual. Include the impact: what breaks, what data is at risk, what user-visible behavior changes.}

## Expected Behavior

{What should happen according to requirements, design, or user expectations.}

## Actual Behavior

{What actually happens. Include error messages, wrong output, crash details, or observable deviation from Expected Behavior.}

## Evidence

{Concrete evidence: code snippets, log lines, trace output, diff, reproduction steps. Must be specific enough to locate the problem without guesswork.}

## Recommendation

{Actionable fix: what to change, where, and why. Include the code path that needs modification.}

## Acceptance Criteria

- [ ] AC1: {Observable, testable condition that resolves the issue.}
- [ ] AC2: {Boundary case, regression check, or safety condition.}

## Suggested Verification

{How an independent verifier should confirm the fix works: specific test commands, test files to run, reproduction steps to try, or assertions to check.}
```

## Status Gate

Incomplete tickets must stay `DRAFT`. A ticket may become `OPEN` only when it has real, non-placeholder content in Description, Evidence, Acceptance Criteria, and Suggested Verification.
