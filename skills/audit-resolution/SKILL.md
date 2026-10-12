---
name: audit-resolution
description: "Use when the user wants to implement fixes for audit tickets. Default to one unblocked ticket from audit next. Resolution records evidence and stops at READY_FOR_VERIFICATION; it never writes PASS."
tags: [audit, resolution, fix, ticket, evidence]
---

# Audit Resolution

Read the [runtime invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation) first. Use the bundled Python CLI after resolving `AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` as described there. A separately configured `audit_*` MCP server is an optional equivalent with an explicit absolute `root`.

Purpose: fix one unblocked audit ticket, record implementation evidence, and hand off to independent verification.

If the user authorized a fix group or batch, inspect `related_tickets` from
`next --for resolution --json` and the full acceptance criteria of each ticket.
Resolve compatible shared-file/root-cause problems through one coherent source
change, then record resolution evidence on each addressed ticket. Do not treat
same-file suggestions as automatic authorization for extra work.


Use the shared [resolution proof guide](../../docs/audit/references/resolution-proof.md) to separate proposed checks, observed results, and verdicts, including whether corrected source is active in the relevant running instance. Keep the existing acceptance gates and user-authorized validation scope; do not generate tests or restart services implicitly.

## First move from empty context

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for resolution --json
```

If the workspace is absent or no ticket is returned, report it without initializing or inventing tickets. A `BLOCKED` ticket requires an explicit resume after its blocker is removed; it is not selected automatically. Before changing implementation, confirm `Decision: FIX` and that every dependency is `PASS`, even for a ticket explicitly named by the user.

## Default flow

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for resolution --json
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" show 001
# inspect current code, implement the smallest correct fix
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" resolve 001   --fix-commit abc123   --evidence "Implemented null-user validation in src/parser.py"   --test "manual reproducer: pass"   --changed src/parser.py   --as audit-resolution   --json
```

## Allowed actions

- read the ticket and related code;
- modify implementation code for the selected ticket;
- record changed files, fix commit, command/result evidence, and resolution notes;
- set `READY_FOR_VERIFICATION` through `python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" resolve`.

## Forbidden actions

- never set `PASS`;
- never verify your own fix;
- do not bypass dependencies;
- do not process all tickets unless the user explicitly asks for batch/all.

## Stop condition

Stop after the selected ticket reaches `READY_FOR_VERIFICATION` and summarize what verification should check. Report command failures from their actual exit/result. If metadata was written but an opted-in Git commit failed, report both facts; do not repeat the resolution as though nothing changed.
