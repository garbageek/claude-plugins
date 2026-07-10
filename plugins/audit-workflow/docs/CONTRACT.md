# Audit Ticket Workflow Contract

This document defines the canonical behavioral contract shared by the audit-ticket skills, agents, CLI, hooks, and MCP server. All operational references must derive from this file instead of duplicating status tables or lifecycle rules.

---

## 1. Canonical CLI Invocation

Cold-start rule: if the project has no `audit/` directory yet, initialize it first:

```bash
python /path/to/audit-discovery/scripts/audit --root /path/to/project init
```

`init` is idempotent and creates the expected audit directories plus lightweight onboarding docs. Models must prefer `init` over manually creating folders.

The bundled CLI is the required command surface:

```bash
python /path/to/audit-discovery/scripts/audit --root /path/to/project <command>
```

The CLI is directly copyable as a single file:

```bash
cp /path/to/audit-discovery/scripts/audit ./audit-cli
python ./audit-cli <command>
```

Project-specific wrappers are allowed only as optional adapters.

---

## 2. Canonical Status Enum

Persisted statuses:

```text
DRAFT                    # incomplete ticket; not eligible for resolution
OPEN                     # evidence-ready ticket accepted for resolution
READY_FOR_VERIFICATION   # fix implemented; independent verification pending
PASS                     # independently verified complete
PARTIAL                  # some criteria met; remaining work exists
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

---

## 3. Role Ownership

Every status-changing command must pass `--as <actor>`. Unknown or missing actors are rejected.

| Actor | May set statuses |
|-------|------------------|
| `audit-discovery` | `DRAFT`, `OPEN` |
| `audit-resolution` | `READY_FOR_VERIFICATION`, `BLOCKED`, `WONTFIX` |
| `audit-verification` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, `INVALID` |

Core rule: `audit-resolution` must never write `PASS`.

`audit-triage` is intentionally not a lifecycle actor. Triage commands may update scheduling and dependency metadata, but they must not gain lifecycle-status write permission by being added to the actor map for symmetry.

---

## 4. State Machine

A transition must satisfy both the current-state transition table and actor ownership.

| Current | Allowed next statuses |
|---------|------------------------|
| `DRAFT` | `OPEN`, `INVALID` |
| `OPEN` | `READY_FOR_VERIFICATION`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `READY_FOR_VERIFICATION` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `PARTIAL` | `READY_FOR_VERIFICATION`, `PASS`, `FAIL`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `FAIL` | `READY_FOR_VERIFICATION`, `WONTFIX`, `INVALID`, `BLOCKED` |
| `REGRESS` | `READY_FOR_VERIFICATION`, `PASS`, `PARTIAL`, `FAIL`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `BLOCKED` | `OPEN`, `READY_FOR_VERIFICATION`, `PASS`, `PARTIAL`, `FAIL`, `WONTFIX`, `INVALID` |
| `PASS` | `REGRESS` |
| `WONTFIX` | `OPEN` |
| `INVALID` | `OPEN` |

Runtime implementations must expose this exact matrix. The copyable single-file CLI mode and module-import mode must not diverge; changes to statuses, actors, transitions, or filename parsing require a parity update for both runtime paths in the same change.

---

## 5. Evidence Gates

### `DRAFT → OPEN`

`OPEN` requires real, non-placeholder content in:

- `## Description`
- `## Evidence`
- `## Acceptance Criteria`
- `## Suggested Verification`

Incomplete tickets stay `DRAFT` and are excluded from `audit next --for resolution`.

Placeholder content includes HTML comments, `TODO`, and brace placeholders such as `{description}` or `{path/to/file.py}`.

### `OPEN → READY_FOR_VERIFICATION`

Resolution requires:

- `--fix-commit`
- `--evidence`
- `--test`
- actor `audit-resolution`

Use:

```bash
audit resolve 042 \
  --fix-commit abc123 \
  --evidence "Regression test added: tests/test_parser.py::test_null_input" \
  --test "pytest tests/test_parser.py: pass" \
  --changed src/parser.py \
  --as audit-resolution
```

### `READY_FOR_VERIFICATION → PASS`

`PASS` requires:

- actor `audit-verification`
- `--verified-commit`
- verdict text
- evidence/test record
- passing result for every acceptance criterion (`AC1`, `AC2`, ...)

Use:

```bash
audit verify 042 \
  --status PASS \
  --verified-commit def456 \
  --criterion "AC1: pass - pytest tests/test_parser.py::test_null_input" \
  --evidence "Manual reproducer no longer fails" \
  --test "pytest tests/test_parser.py: pass" \
  --verdict "Fixed and covered" \
  --as audit-verification
```

---

## 6. Canonical Verification File Schema

```markdown
# Verification: NNN-CATEGORY-slug

**Original Ticket:** `audit/tickets/NNN-CATEGORY-slug.md`
**Original Category:** `CATEGORY`
**Original Severity:** `critical|high|medium|low`
**Verification Status:** `DRAFT|OPEN|READY_FOR_VERIFICATION|PASS|PARTIAL|FAIL|REGRESS|BLOCKED|WONTFIX|INVALID`
**Resolved Date:** `YYYY-MM-DD` or empty until resolved
**Resolved By:** `audit-resolution` or empty until resolved
**Verified Date:** `YYYY-MM-DD` or empty until independently verified
**Verified By:** `audit-verification` or empty until independently verified
**Fix Commit:** `sha` or empty until resolved
**Verified Commit:** `sha` or empty until independently verified

## Original Issue

## Resolution Evidence

## Criteria Results

## Verification Checklist

## Current State

## Evidence

## Test Verification

## Verdict
```

Backward compatibility: parsers may read legacy `**Status:**`, `**Date:**`, and `**Commit Verified At:**`, but new writes must use the canonical fields above.

---

## 7. Canonical Ticket Metadata

Ticket files must use the filename format `{NNN}-{CATEGORY}-{slug}.md` and category enum:

```text
BUG
DEGRADED
LOST
TODO
TEST
CONFIG
SECURITY
CODE-QUALITY
```

Tickets also carry machine-readable fields:

```markdown
**Depends On:** `none` or `003, 007`
**Blocks:** `none` or `012`
**Impact:** `1-5`
**Effort:** `1-5`
**Priority:** `1-25`
**P-level:** `P0|P1|P2|P3`
**Decision:** `FIX|DEFER|WONTFIX|DUPLICATE`
**Phase:** `critical-path|quick-wins|feature-parity|backlog|...`
```

`audit next --for resolution` consumes this metadata plus dependency edges.

---

## 8. Dependency Semantics

Canonical edge meaning:

```text
003 blocks 001
```

Meaning: ticket `001` depends on ticket `003` and should not be selected for resolution until `003` is resolved.

Equivalent ticket field:

```markdown
**Depends On:** `003`
```

`audit doctor` rejects missing dependency targets, cycles, and dependencies that are unusable (`FAIL`, `BLOCKED`, `INVALID`).

---

## 9. Git and Commit Ownership

| Action | Who may do it | Default |
|--------|---------------|---------|
| Implementation commit | `audit-resolution` | Project workflow dependent; never automatic from docs alone. |
| Verification metadata update | `audit-verification` | File write only by default. |
| Audit metadata commit | `audit` CLI | Opt-in via `--git-commit`; checks dirty worktree first. |

`--git-commit` fails on a dirty worktree unless `--allow-dirty` is explicitly passed.

---

## 10. Doctor Fix Semantics

`audit doctor` reports the current audit workflow health.

`audit doctor --fix` may create missing directories, onboarding files, or verification stubs. After applying any fix, the user-visible final result must be based on a fresh re-check, not on the pre-fix issue list.

A command may report both the fix attempt and the re-check, but the final issue count must represent the post-fix state.

---

## 11. Machine-Readable Output

When `--json` is passed:

- stdout contains JSON only;
- human output is suppressed;
- failed batch updates return non-zero exit status;
- batch JSON contains per-ID `updated` and `failed` arrays.

MCP tools must return structured JSON text in the MCP content envelope. If the wrapped CLI command emits human text, the MCP layer must normalize it into a JSON object and preserve the raw text in a named field such as `stdout_text`.

MCP `audit_create` has an explicit cold-start side effect: it runs `audit init` before ticket creation. The tool result must expose both initialization and creation results, and must not continue to creation if initialization fails.

---

## 12. Reporting Source of Truth

The canonical source of truth is the normalized record produced by:

```bash
audit export --json
```

Reports and baselines should derive from this model rather than re-parsing different subsets independently. Baselines include status, semantic metadata, and content hashes.

`docs/references/runtime-diagnosis-patterns.md` is a maintained operational reference and must be updated when runtime diagnosis behavior changes.
