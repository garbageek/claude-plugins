---
name: audit-init
description: Initialize the audit ticket workspace when the user explicitly requests audit lifecycle setup. Preserve existing records and report health and queues. Not a prerequisite for read-only code review.
---

# Initialize Audit Workspace

Read the [audit invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation).
Resolve the installed plugin and target project separately. Prefer the `audit_*`
MCP tools with an explicit absolute `root`; use CLI only after setting
`AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` to the observed paths. Never create
project state in the installed plugin directory.

Call `audit_init(root=...)`, then `audit_doctor(root=...)` and
`audit_summary(root=...)`. Initialization is idempotent; preserve existing state.
A read-only review or status question does not authorize initialization.

CLI equivalent, after resolving the two paths above:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

Report the actual created or existing workspace, doctor findings, and queue.
Do not silently apply `doctor --fix`, create tickets, or commit changes.
