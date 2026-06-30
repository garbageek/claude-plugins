---
name: audit-discovery
description: "Use when findings should be recorded as structured audit tickets. Cold-start friendly: initialize the audit workflow, inspect evidence, then create DRAFT/OPEN tickets. Do not resolve or verify tickets."
tags: [audit, discovery, ticket, evidence, workflow]
---

# Audit Discovery

Purpose: convert concrete findings into audit tickets. The CLI/MCP runtime is the source of truth; Markdown files are the human-readable record.

## First move from empty context

Prefer MCP tools when available. CLI fallback:

```bash
audit init
audit doctor
audit summary
```

If `audit/` does not exist, that is normal. Run `audit init`; do not create the structure by hand.

## Modes

| Mode | Write audit files? | Behavior |
|---|---:|---|
| Investigate | No | Read code/logs and explain what is known. |
| Ticketize | Yes | Create tickets only for evidence-backed findings. |
| Audit sweep | Yes | Systematically inspect, then ticketize concrete findings. |

## Create tickets

Incomplete finding:

```bash
audit create BUG --title "parse failure on null input" --severity high --module src/parser.py
```

Evidence-ready ticket:

```bash
audit create BUG   --title "parse failure on null input"   --severity high   --module src/parser.py   --description "Parser crashes when payload.user is null."   --evidence "src/parser.py:42 dereferences payload['user']['id'] without a guard"   --acceptance-criterion "Null user payload returns a typed validation error"   --suggested-verification "Reproduce null-user payload and verify typed validation error"   --open   --json
```

## Allowed actions

- initialize the workflow;
- create `DRAFT` or `OPEN` tickets;
- promote evidence-ready `DRAFT` tickets to `OPEN` using `audit open ... --as audit-discovery`;
- add concrete evidence, acceptance criteria, module/line references, and suggested verification.

## Forbidden actions

- do not implement fixes;
- do not set `READY_FOR_VERIFICATION`;
- do not set `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `WONTFIX`, or `INVALID` except through the appropriate role;
- do not invent tickets from vague suspicions.

## Stop condition

Stop after tickets are created/opened and hand off to `audit-triage` or `audit-resolution`.
