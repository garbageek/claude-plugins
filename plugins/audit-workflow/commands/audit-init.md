---
description: Initialize the audit workflow in the current project and show health/status.
---

Initialize the Audit Workflow plugin state in this project.

Run:

```bash
audit init
audit doctor
audit summary
```

If the workflow already exists, keep going; `audit init` is idempotent. Report the created or existing `audit/` tree and the current queue summary.
