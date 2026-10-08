---
name: audit-next
description: Find the next eligible ticket for resolution or independent verification in an existing audit workspace. Use for queue selection without changing state.
---

# Select the Next Audit Ticket

Read the [audit invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation).
Resolve the installed plugin and target project separately. Prefer the `audit_*`
MCP tools with an explicit absolute `root`; use CLI only after setting
`AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` to the observed paths. Never create
project state in the installed plugin directory.

Use the requested queue (`resolution` or `verification`); without a choice, show
both. If no audit workspace exists, report it without initialization. Call
`audit_next(root=..., for_role=...)`; this selects work but does not execute it.

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for resolution --json
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for verification --json
```

Show the returned ticket ID, status, severity, title and selection reason. State
an empty queue accurately. Do not claim a blocked ticket ready or automatically
start resolution/verification from a queue-inspection request.
