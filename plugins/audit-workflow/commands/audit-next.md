---
description: Show the next audit ticket for resolution or verification.
argument-hint: "resolution|verification"
---

Find the next ticket. Use the requested queue if provided; otherwise show both.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for verification --json
```

If a ticket is returned, show the ticket ID, status, severity, title, and why it is next.
