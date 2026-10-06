---
description: Initialize the audit workflow in the current project and show health/status.
---

Initialize the Audit Workflow plugin state in this project.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" summary
```

If the workflow already exists, keep going; `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init` is idempotent. Report the created or existing `audit/` tree and the current queue summary.
