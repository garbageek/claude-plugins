---
name: audit-triage
description: "Use when existing audit tickets need prioritization, dependency ordering, or a roadmap. Triage must write executable metadata consumed by audit next; do not create tickets or edit implementation code."
tags: [audit, triage, priority, dependency, roadmap]
---

# Audit Triage

Prefer the structured `audit_*` MCP tools when available. Use the bundled CLI only as fallback: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" <command> ...`.

Purpose: turn an audit queue into executable ordering. A prose plan is optional; `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution` must consume the metadata.

## First move from empty context

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" export --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" summary
```

If no tickets exist, report an empty queue. Do not create findings during triage.

## Update executable metadata

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" deps add 001 --depends-on 003
```

Dependency semantics:

```text
003 blocks 001
```

Ticket `001` is skipped by `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution` until `003` is resolved.

## Scoring

| Field | Values | Meaning |
|---|---|---|
| Impact | 1-5 | User/data/release impact |
| Effort | 1-5 | Implementation effort |
| Priority | 1-25 | `Impact × (6 - Effort)` |
| P-level | P0-P3 | Execution priority |
| Decision | FIX/DEFER/WONTFIX/DUPLICATE | Operational decision |
| Phase | critical-path/quick-wins/feature-parity/backlog | Execution group |

## Allowed actions

- read tickets and canonical export;
- set triage metadata;
- add dependency edges;
- write optional roadmap files under `audit/triage/`.

## Forbidden actions

- do not create tickets unless the user explicitly switches to discovery;
- do not edit implementation code;
- do not resolve or verify tickets;
- do not mark tickets `PASS`.

## Stop condition

Stop when `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution --json` returns the expected highest-priority unblocked ticket.
