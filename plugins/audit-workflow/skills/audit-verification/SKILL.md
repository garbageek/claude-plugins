---
name: audit-verification
description: "Use when resolved audit tickets need independent verification. Default to the next READY_FOR_VERIFICATION ticket. Verification may write PASS/PARTIAL/FAIL with criterion evidence; it should not edit implementation code."
tags: [audit, verification, validate, verdict, evidence]
---

# Audit Verification

Read the [runtime invocation contract](../../docs/CONTRACT.md#1-canonical-runtime-invocation) first. Prefer the structured `audit_*` MCP tools with an explicit absolute `root`. For CLI fallback, resolve `AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` as described there.

Purpose: independently verify resolved tickets against the original acceptance criteria and current code state.

If this agent/session implemented the fix, hand verification to a fresh native
subagent or another session with this skill, the project root, ticket IDs, fix
revision, and original criteria. Do not treat switching the role name as
independent verification. Without an independent reviewer, leave the ticket
awaiting verification and report the handoff; do not write PASS.


Use the shared [resolution proof guide](../../docs/references/resolution-proof.md) to separate proposed checks, observed results, and verdicts, including whether corrected source is active in the relevant running instance. Keep the existing acceptance gates and user-authorized validation scope; do not generate tests or restart services implicitly.

## First move from empty context

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for verification --json
```

If no ticket is returned, report that nothing is awaiting verification. Do not create or resolve tickets.

## PASS flow

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" show 001
# inspect code and evidence independently
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" verify 001   --status PASS   --verified-commit def456   --criterion "AC1: pass - null-user payload returns typed validation error"   --evidence "Manual reproducer no longer fails"   --test "manual reproducer: pass"   --verdict "All acceptance criteria satisfied"   --as audit-verification   --json
```

Use `PARTIAL` or `FAIL` when evidence is incomplete or a criterion is not satisfied.

## Allowed actions

- read ticket, verification record, code, and resolution evidence;
- run independent checks/commands needed to validate the result;
- set `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, or `INVALID` through `python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" verify`.

## Forbidden actions

- do not edit implementation code;
- do not perform resolution work;
- do not mark `PASS` without criterion evidence and a verified commit;
- do not invent missing acceptance criteria.

## Stop condition

Stop after writing the independent verdict and summarize the reason.
