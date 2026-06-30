---
name: audit-verification
description: "Use when resolved audit tickets need independent verification. Default to the next READY_FOR_VERIFICATION ticket. Verification may write PASS/PARTIAL/FAIL with criterion evidence; it should not edit implementation code."
tags: [audit, verification, validate, verdict, evidence]
---

# Audit Verification

Purpose: independently verify resolved tickets against the original acceptance criteria and current code state.

## First move from empty context

```bash
audit init
audit doctor
audit next --for verification --json
```

If no ticket is returned, report that nothing is awaiting verification. Do not create or resolve tickets.

## PASS flow

```bash
audit show 001
# inspect code and evidence independently
audit verify 001   --status PASS   --verified-commit def456   --criterion "AC1: pass - null-user payload returns typed validation error"   --evidence "Manual reproducer no longer fails"   --test "manual reproducer: pass"   --verdict "All acceptance criteria satisfied"   --as audit-verification   --json
```

Use `PARTIAL` or `FAIL` when evidence is incomplete or a criterion is not satisfied.

## Allowed actions

- read ticket, verification record, code, and resolution evidence;
- run independent checks/commands needed to validate the result;
- set `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, or `INVALID` through `audit verify`.

## Forbidden actions

- do not edit implementation code;
- do not perform resolution work;
- do not mark `PASS` without criterion evidence and a verified commit;
- do not invent missing acceptance criteria.

## Stop condition

Stop after writing the independent verdict and summarize the reason.
