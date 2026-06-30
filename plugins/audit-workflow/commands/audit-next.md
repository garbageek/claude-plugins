---
description: Show the next audit ticket for resolution or verification.
argument-hint: "resolution|verification"
---

Find the next ticket. Use the requested queue if provided; otherwise show both.

```bash
audit init
audit next --for resolution --json
audit next --for verification --json
```

If a ticket is returned, show the ticket ID, status, severity, title, and why it is next.
