---
name: audit-status
description: Inspect existing audit health, summary, and resolution or verification queues. Use for status questions; do not initialize or change audit state.
---

# Inspect Audit Status

Read the [audit invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation).
Resolve the installed plugin and target project separately. Use the bundled
Python CLI after setting `AUDIT_PLUGIN_ROOT` and `AUDIT_PROJECT_DIR` to the
observed paths. A separately configured `audit_*` MCP server is optional and
requires an explicit absolute project `root`. Never create project state in
the installed plugin directory.

If the selected project has no `audit/` directory, report that no audit workspace
exists and stop without creating one. Otherwise run CLI `doctor`, `summary`,
and `next` for the requested queues using the selected project root.

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for resolution --json
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" next --for verification --json
```

Report observed counts, next work and health problems. Do not run `init` or
`doctor --fix`; missing evidence is not a completed verdict.
