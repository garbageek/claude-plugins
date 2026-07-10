# Audit Ticket Protocol

This document is the operational quick reference for using the audit workflow.

`CONTRACT.md` is the canonical source for statuses, actors, state transitions, evidence gates, field schemas, dependency semantics, machine-readable output, and compatibility rules. Do not duplicate those tables here. Any behavioral change must update `CONTRACT.md` first, then this protocol only when the operator-facing procedure changes.

---

## Cold Start

If the target project has no audit workflow yet, run:

```bash
audit init
audit doctor
```

Do not manually create the directory structure unless the CLI is unavailable. `audit init` is idempotent and creates the directories/docs expected by all four skills.

For MCP clients, `audit_create` may perform this initialization as an explicit cold-start side effect before creating the first ticket. The MCP result must report both the initialization result and the create result.

---

## Required Command Surface

Use the bundled CLI for lifecycle changes:

```bash
audit <command> [options]
```

Status-changing commands must pass an explicit `--as <actor>` and must satisfy the canonical actor ownership and state transition rules in `CONTRACT.md`.

Normal handoff commands:

```bash
audit open 042 --as audit-discovery

audit resolve 042 \
  --fix-commit abc123 \
  --evidence "Implementation evidence" \
  --test "Verification command/result" \
  --as audit-resolution

audit verify 042 \
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
audit create BUG \
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
audit triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path
audit deps add 001 --depends-on 003
```

Dependency semantics are defined once in `CONTRACT.md`.

---

## Doctor and Fix Semantics

`audit doctor` diagnoses workflow consistency.

`audit doctor --fix` may create missing workflow directories, onboarding files, or verification stubs. After applying fixes, the command surface must re-check the current state before reporting the final issue count. It must not print stale pre-fix issues as the final result.

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
audit export --json
```

Automation must consume this normalized model instead of independently re-parsing partial Markdown subsets.

`--json` stdout must contain JSON only. Batch mutations must return non-zero if any requested item failed.

---

## Runtime Diagnosis Reference

`docs/references/runtime-diagnosis-patterns.md` is a maintained operational reference for diagnosing runtime workflow failures. Keep it aligned with the CLI, hooks, and MCP behavior when those behavior surfaces change.
