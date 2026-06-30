# Audit Ticket Protocol

## Cold Start

If the target project has no audit workflow yet, run:

```bash
audit init
audit doctor
```

Do not manually create the directory structure unless the CLI is unavailable. `audit init` is idempotent and creates the directories/docs expected by all four skills.

Invariants that all four skills and the `audit` CLI must obey. Violations are bugs.

## Canonical Statuses

Persisted statuses:

```text
DRAFT                    # incomplete ticket; not eligible for resolution
OPEN                     # evidence-ready ticket accepted for resolution
READY_FOR_VERIFICATION   # fix implemented; independent verification pending
PASS                     # independently verified complete
PARTIAL                  # some criteria passed; remaining work exists
FAIL                     # fix missing, incorrect, or insufficient
REGRESS                  # previously passing behavior broke again
BLOCKED                  # cannot proceed due dependency/access/context
WONTFIX                  # deliberate decision not to fix
INVALID                  # original ticket wrong, obsolete, or duplicate
```

Derived display-only state:

```text
UNVERIFIED               # no paired verification file exists; never persisted
```

## State Machine

A transition is valid only when both conditions hold:

1. current status allows the target status;
2. the explicit actor passed via `--as` may write the target status.

```text
DRAFT
  → OPEN
  → INVALID

OPEN
  → READY_FOR_VERIFICATION
  → BLOCKED
  → WONTFIX
  → INVALID

READY_FOR_VERIFICATION
  → PASS
  → PARTIAL
  → FAIL
  → REGRESS
  → BLOCKED
  → WONTFIX
  → INVALID

PARTIAL
  → READY_FOR_VERIFICATION
  → PASS
  → FAIL
  → BLOCKED
  → WONTFIX
  → INVALID

FAIL
  → READY_FOR_VERIFICATION
  → WONTFIX
  → INVALID
  → BLOCKED

REGRESS
  → READY_FOR_VERIFICATION
  → PASS
  → PARTIAL
  → FAIL
  → BLOCKED
  → WONTFIX
  → INVALID

BLOCKED
  → OPEN
  → READY_FOR_VERIFICATION
  → PASS
  → PARTIAL
  → FAIL
  → WONTFIX
  → INVALID

PASS
  → REGRESS

WONTFIX
  → OPEN

INVALID
  → OPEN
```

## Lifecycle Ownership

Every status-changing command must pass `--as <actor>`. Missing or unknown actors are rejected.

| Actor | May write statuses | Must not write |
|-------|--------------------|----------------|
| `audit-discovery` | `DRAFT`, `OPEN` | implementation or verification statuses |
| `audit-resolution` | `READY_FOR_VERIFICATION`, `BLOCKED`, `WONTFIX` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `OPEN` |
| `audit-verification` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, `INVALID` | `OPEN`, `READY_FOR_VERIFICATION` |

Core rule: `audit-resolution` must never write `PASS`.

## Evidence Gates

### `DRAFT → OPEN`

`OPEN` requires non-placeholder content in:

- `## Description`
- `## Evidence`
- `## Acceptance Criteria`
- `## Suggested Verification`

Incomplete tickets remain `DRAFT` and are excluded from `audit next --for resolution`.

### `OPEN → READY_FOR_VERIFICATION`

Use `audit resolve`, not a generic update, for normal implementation handoff.

Required:

- actor `audit-resolution`;
- `--fix-commit`;
- `--evidence`;
- `--test`.

This updates `Resolved Date`, `Resolved By`, `Fix Commit`, and resolution evidence. It must not fill `Verified Date` or `Verified By`.

### `READY_FOR_VERIFICATION → PASS`

Use `audit verify`.

Required:

- actor `audit-verification`;
- `--verified-commit`;
- `--verdict`;
- verification evidence and test result;
- passing criterion evidence for every acceptance criterion (`AC1`, `AC2`, ...).

## Canonical Ticket Fields

Ticket files use `{NNN}-{CATEGORY}-{slug}.md` and carry:

```markdown
**Category:** `BUG|DEGRADED|LOST|TODO|TEST|CONFIG|SECURITY|CODE-QUALITY`
**Severity:** `critical|high|medium|low`
**Module:** `path/or/component`
**Lines:** `N-M` or `N/A`
**Source:** `log analysis|code review|runtime trace|...`
**Depends On:** `none` or `003, 007`
**Blocks:** `none` or `012`
**Impact:** `1-5`
**Effort:** `1-5`
**Priority:** `1-25`
**P-level:** `P0|P1|P2|P3`
**Decision:** `FIX|DEFER|WONTFIX|DUPLICATE`
**Phase:** `critical-path|quick-wins|feature-parity|backlog|...`
```

`audit next --for resolution` consumes the status, priority fields, decision, phase, and dependency metadata.

## Canonical Verification Fields

```markdown
**Verification Status:** `DRAFT|OPEN|READY_FOR_VERIFICATION|PASS|PARTIAL|FAIL|REGRESS|BLOCKED|WONTFIX|INVALID`
**Resolved Date:** `YYYY-MM-DD` or empty until resolved
**Resolved By:** `audit-resolution` or empty until resolved
**Verified Date:** `YYYY-MM-DD` or empty until independently verified
**Verified By:** `audit-verification` or empty until independently verified
**Fix Commit:** `sha` or empty until resolved
**Verified Commit:** `sha` or empty until independently verified
```

`## Verdict` is the canonical verdict section. Status history is only an audit trail.

## Dependency Semantics

Canonical edge meaning:

```text
003 blocks 001
```

Meaning: ticket `001` depends on ticket `003`; ticket `001` must not be selected for resolution until `003` is resolved.

Equivalent ticket field:

```markdown
**Depends On:** `003`
```

`audit doctor` rejects missing dependency targets, cycles, and unusable dependencies (`FAIL`, `BLOCKED`, `INVALID`).

## Reporting and Automation

- `audit export --json` is the canonical normalized machine-readable source of truth.
- `--json` output must contain JSON only on stdout.
- Batch mutations return non-zero if any item failed.
- Generated Markdown reports must escape table cell contents.
- Baselines must include status, semantic fields, and content hashes.

## Git Safety

`--git-commit` is opt-in. It checks the worktree first and fails if dirty unless `--allow-dirty` is explicitly passed.
