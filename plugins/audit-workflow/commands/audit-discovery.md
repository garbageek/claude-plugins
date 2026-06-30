---
description: Run the audit discovery role to inspect evidence and create audit tickets.
argument-hint: "scope or files/logs to inspect"
---

Use the `audit-discovery` skill/agent.

Start:

```bash
audit init
audit doctor
```

Inspect the requested scope. Create tickets only for concrete evidence-backed findings using `audit create`. Do not resolve or verify tickets.
