---
description: Run the audit verification role on the next or specified resolved ticket.
argument-hint: "optional ticket ID"
---

Use the `audit-verification` skill/agent.

Start:

```bash
audit init
audit doctor
audit next --for verification --json
```

Verify independently and write the final verdict through `audit verify ... --as audit-verification`. Do not edit implementation code.
