---
name: audit-discovery
description: "Use when findings should be recorded as structured audit tickets. Cold-start friendly: initialize the audit workflow, inspect evidence, then create DRAFT/OPEN tickets. Do not resolve or verify tickets."
tags: [audit, discovery, ticket, evidence, workflow]
---

# Audit Discovery

Read the [runtime invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation) first. Prefer the structured `audit_*` MCP tools with an explicit absolute `root`. For CLI fallback, resolve `AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` as described there.

Purpose: convert concrete findings into audit tickets. The CLI/MCP runtime is the source of truth; Markdown files are the human-readable record.

## First move from empty context

Prefer MCP tools when available. CLI fallback:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

If `audit/` does not exist, that is normal. Run `python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init`; do not create the structure by hand.

## Modes

| Mode | Write audit files? | Behavior |
|---|---:|---|
| Investigate | No | Read code/logs and explain what is known. |
| Ticketize | Yes | Create tickets only for evidence-backed findings. |
| Audit sweep | Yes | Systematically inspect, then ticketize concrete findings. |

## Create tickets

Incomplete finding:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" create BUG --title "parse failure on null input" --severity high --module src/parser.py
```

Evidence-ready ticket:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" create BUG   --title "parse failure on null input"   --severity high   --module src/parser.py   --description "Parser crashes when payload.user is null."   --evidence "src/parser.py:42 dereferences payload['user']['id'] without a guard"   --acceptance-criterion "Null user payload returns a typed validation error"   --suggested-verification "Reproduce null-user payload and verify typed validation error"   --open   --json
```

## Allowed actions

- initialize the workflow;
- create `DRAFT` or `OPEN` tickets;
- promote evidence-ready `DRAFT` tickets to `OPEN` using `python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" open ... --as audit-discovery`;
- add concrete evidence, acceptance criteria, module/line references, and suggested verification.

## Forbidden actions

- do not implement fixes;
- do not set `READY_FOR_VERIFICATION`;
- do not set `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `WONTFIX`, or `INVALID` except through the appropriate role;
- do not invent tickets from vague suspicions.

## Stop condition

Stop after tickets are created/opened and hand off to `audit-triage` or `audit-resolution`.
