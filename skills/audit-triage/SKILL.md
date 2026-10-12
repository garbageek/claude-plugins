---
name: audit-triage
description: "Use when existing audit tickets need prioritization, dependency ordering, shared-file or shared-cause fix groups, or a roadmap. Do not create tickets or edit implementation code."
tags: [audit, triage, priority, dependency, roadmap]
---

# Audit Triage

Read the [runtime invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation) first. Use the bundled Python CLI after resolving `AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` as described there. A separately configured `audit_*` MCP server is an optional equivalent with an explicit absolute `root`.

Purpose: plan coherent fixes across tickets, not just assign statuses. Resolve
dependencies and shared-change opportunities, then write decisions, scores,
phases, and fix groups to ticket headers. A prose roadmap is optional;
`next --for resolution` reads only ticket state.

## First move from empty context

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" export --json
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

If the workspace is absent or no tickets exist, report that state without initializing it. Do not create findings during triage. Treat dependency-wait warnings separately from structural errors; a pending prerequisite is not a corrupt audit.

## Update executable metadata

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" triage set 001 --impact 5 --effort 2 --p-level P0 --decision FIX --phase critical-path
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" deps add 001 --depends-on 003
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" triage set 001 --fix-group shared-parser-fix
```

Dependency semantics:

```text
003 blocks 001
```

Ticket `001` is skipped by `python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for resolution` until `003` reaches `PASS`.

## Scoring

| Field | Values | Meaning |
|---|---|---|
| Impact | 1-5 | User/data/release impact |
| Effort | 1-5 | Implementation effort |
| Priority | 1-25 | `Impact × (6 - Effort)` |
| P-level | P0-P3 | Execution priority |
| Decision | FIX/DEFER/WONTFIX/DUPLICATE | Operational decision |
| Phase | critical-path/quick-wins/feature-parity/backlog | Execution group |
| Fix Group | Optional short slug | Tickets that can share one coherent code change |

## Grouping and scheduling

- Inspect affected files, call paths, overlapping changes and underlying causes
  before choosing groups. Prefer one coherent edit session for compatible issues
  in the same source file or a shared component, rather than repeating the same
  investigation and patch multiple times.
- Assign the same `--fix-group` only when work can actually be resolved together.
  Shared files alone are a suggestion, not proof of a shared fix; identify
  conflicting edits and dependencies before grouping.
- Use `deps add/remove` for genuine prerequisites. A deferred, rejected or
  blocked ticket must not become executable merely because its file matches a
  selected group. Only PASS dependencies unblock resolution.
- Apply every triage decision through the CLI *before* producing a report or
  roadmap. The report is derived from `export --json` and never feeds the queue.
- Check `next --for resolution --json`: `ticket` is the selection;
  `related_tickets` are additional *eligible* FIX suggestions for shared work,
  not automatically authorized extra tickets.

## Allowed actions

- read tickets and canonical export;
- set triage metadata;
- add or remove dependency edges;
- write optional roadmap files under `audit/triage/`.

## Forbidden actions

- do not create tickets unless the user explicitly switches to discovery;
- do not edit implementation code;
- do not resolve or verify tickets;
- do not mark tickets `PASS`.

## Stop condition

Stop when `doctor` accepts the metadata and `next --for resolution --json`
returns the expected highest-priority unblocked ticket and coherent suggestions.
