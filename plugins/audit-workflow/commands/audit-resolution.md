---
description: Run the audit resolution role on the next or specified ticket.
argument-hint: "optional ticket ID"
---

Use the `audit-resolution` skill/agent.

Start:

```bash
audit init
audit doctor
audit next --for resolution --json
```

Resolve one unblocked ticket unless the user explicitly requested a batch. Stop at `READY_FOR_VERIFICATION`; never set `PASS`.
