---
description: Show audit workflow health, summary, and next queued work.
---

Show current audit workflow status.

Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" summary
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for resolution --json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" next --for verification --json
```

Summarize only the actionable queue and any doctor findings.
