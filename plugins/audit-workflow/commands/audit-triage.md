---
description: Run the audit triage role to prioritize tickets and model dependencies.
argument-hint: "optional triage scope"
---

Use the `audit-triage` skill/agent.

Start:

```bash
audit init
audit export --json
audit summary
```

Set executable metadata through `audit triage set` and `audit deps add`, then confirm selection with `audit next --for resolution --json`.
