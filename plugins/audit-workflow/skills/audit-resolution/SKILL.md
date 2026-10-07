---
name: audit-resolution
description: "Use when the user wants to implement fixes for audit tickets. Default to one unblocked ticket from audit next. Resolution records evidence and stops at READY_FOR_VERIFICATION; it never writes PASS."
tags: [audit, resolution, fix, ticket, evidence]
---

# Audit Resolution

Prefer the structured `audit_*` MCP tools when available. Use the bundled CLI only as fallback: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" <command> ...`.

Purpose: fix one unblocked audit ticket, record implementation evidence, and hand off to independent verification.


Use the shared [resolution proof guide](../../docs/references/resolution-proof.md) to separate proposed checks, observed results, and verdicts, including whether corrected source is active in the relevant running instance. Keep the existing acceptance gates and user-authorized validation scope; do not generate tests or restart services implicitly.

## First move from empty context

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution --json
```

If no ticket is returned, report that no resolution work is queued. Do not invent tickets.

## Default flow

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" show 001
# inspect current code, implement the smallest correct fix
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" resolve 001   --fix-commit abc123   --evidence "Implemented null-user validation in src/parser.py"   --test "manual reproducer: pass"   --changed src/parser.py   --as audit-resolution   --json
```

## Allowed actions

- read the ticket and related code;
- modify implementation code for the selected ticket;
- record changed files, fix commit, command/result evidence, and resolution notes;
- set `READY_FOR_VERIFICATION` through `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" resolve`.

## Forbidden actions

- never set `PASS`;
- never verify your own fix;
- do not bypass dependencies;
- do not process all tickets unless the user explicitly asks for batch/all.

## Stop condition

Stop after the selected ticket reaches `READY_FOR_VERIFICATION` and summarize what verification should check.
