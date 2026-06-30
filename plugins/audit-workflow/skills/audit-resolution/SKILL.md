---
name: audit-resolution
description: "Use when the user wants to implement fixes for audit tickets. Default to one unblocked ticket from audit next. Resolution records evidence and stops at READY_FOR_VERIFICATION; it never writes PASS."
tags: [audit, resolution, fix, ticket, evidence]
---

# Audit Resolution

Purpose: fix one unblocked audit ticket, record implementation evidence, and hand off to independent verification.

## First move from empty context

```bash
audit init
audit doctor
audit next --for resolution --json
```

If no ticket is returned, report that no resolution work is queued. Do not invent tickets.

## Default flow

```bash
audit next --for resolution --json
audit show 001
# inspect current code, implement the smallest correct fix
audit resolve 001   --fix-commit abc123   --evidence "Implemented null-user validation in src/parser.py"   --test "manual reproducer: pass"   --changed src/parser.py   --as audit-resolution   --json
```

## Allowed actions

- read the ticket and related code;
- modify implementation code for the selected ticket;
- record changed files, fix commit, command/result evidence, and resolution notes;
- set `READY_FOR_VERIFICATION` through `audit resolve`.

## Forbidden actions

- never set `PASS`;
- never verify your own fix;
- do not bypass dependencies;
- do not process all tickets unless the user explicitly asks for batch/all.

## Stop condition

Stop after the selected ticket reaches `READY_FOR_VERIFICATION` and summarize what verification should check.
