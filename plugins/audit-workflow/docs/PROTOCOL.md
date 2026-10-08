# Audit Ticket Protocol

This document is the operational quick reference for using the audit workflow.

`CONTRACT.md` is the canonical source for statuses, actors, state transitions, evidence gates, field schemas, dependency semantics, machine-readable output, and compatibility rules. Do not duplicate those tables here. Any behavioral change must update `CONTRACT.md` first, then this protocol only when the operator-facing procedure changes.

---

## Cold Start

For requested ticket-lifecycle work, follow the [invocation contract](CONTRACT.md#1-canonical-runtime-invocation) and pass the absolute project `root` to every MCP tool. If the target project has no audit workflow yet, prefer `audit_init`, then `audit_doctor`. Read-only investigation does not initialize state.

CLI fallback after resolving the paths in the invocation contract:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
```

Do not manually create the directory structure. Initialization is idempotent and creates the directories/docs expected by all four skills.

For MCP clients, `audit_create` may perform this initialization as an explicit cold-start side effect before creating the first ticket. The MCP result must report both the initialization result and the create result.

---

## Required Command Surface

Use the structured MCP tools for normal lifecycle work. The bundled CLI is the fallback surface:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" <command> [options]
```

Status-changing commands must pass an explicit `--as <actor>` and must satisfy the canonical actor ownership and state transition rules in `CONTRACT.md`.

Normal handoff commands:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" open 042 --as audit-discovery

python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" resolve 042 \
  --fix-commit abc123 \
  --evidence "Implementation evidence" \
  --test "Verification command/result" \
  --as audit-resolution

python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" verify 042 \
  --status PASS \
  --verified-commit def456 \
  --criterion "AC1: pass - evidence" \
  --evidence "Independent verification evidence" \
  --test "Verification command/result" \
  --verdict "Fixed and covered" \
  --as audit-verification
```

Core invariant: `audit-resolution` stops at `READY_FOR_VERIFICATION` and must never write `PASS`.

---

## Ticket Creation

Create tickets through the CLI or MCP tool, not by manually writing `audit/tickets/*.md`.

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" create BUG \
  --title "Parser drops empty values" \
  --severity high \
  --module src/parser.py \
  --description "Concrete defect description" \
  --evidence "Observed failure with input X" \
  --acceptance-criterion "AC1: empty values are preserved" \
  --suggested-verification "Run parser on reproducer"
```

Tickets with placeholder-only required sections remain `DRAFT` and are excluded from `audit next --for resolution`. `OPEN` requires real content in the canonical sections listed in `CONTRACT.md`.

---

## Triage Role Boundary

`audit-triage` is intentionally not a lifecycle actor. Triage commands may update scheduling and dependency metadata, but they do not grant permission to write lifecycle statuses.

Use triage commands for priority and dependency work:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" deps add 001 --depends-on 003
```

Dependency semantics are defined once in `CONTRACT.md`.

---

## Doctor and Fix Semantics

`audit_doctor` or CLI `doctor` diagnoses workflow consistency.

`audit_doctor(fix=true)` or CLI `doctor --fix` may create missing workflow directories, onboarding files, or verification stubs. After applying fixes, the command surface must re-check the current state before reporting the final issue count. It must not print stale pre-fix issues as the final result.

MCP `audit_doctor` must return a JSON object with structured fields, even when the underlying CLI emits human text.

---

## Verification Field Compatibility

New writes must use the canonical verification fields from `CONTRACT.md`.

Parsers may read legacy compatibility fields:

- `**Status:**`
- `**Date:**`
- `**Commit Verified At:**`

Compatibility fields are read-only inputs for older records. They are not the write schema for new records.

---

## Reporting and Automation

Use the normalized export as the source of truth:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" export --json
```

Automation must consume this normalized model instead of independently re-parsing partial Markdown subsets.

`--json` stdout must contain JSON only. Batch mutations must return non-zero if any requested item failed.

---

## Runtime Diagnosis Reference

`docs/references/runtime-diagnosis-patterns.md` is a maintained operational reference for diagnosing runtime workflow failures. Keep it aligned with the CLI, hooks, and MCP behavior when those behavior surfaces change.
