# Ticket Dependencies

Write to `audit/triage/dependencies.md` when cross-ticket ordering matters.

## Edges (machine-readable)

```text
# format: <blocking-ticket> blocks <blocked-ticket>
# Uncomment real edges; keep examples commented.
# 003 blocks 001
# 003 blocks 007
```

Meaning: `001` and `007` depend on `003`. They must not be selected by `python3 /path/to/audit-workflow/scripts/audit.py next --for resolution` until `003` is resolved. Remove `#` only for real project edges.

Equivalent CLI form:

```bash
python3 /path/to/audit-workflow/scripts/audit.py deps add 001 --depends-on 003
python3 /path/to/audit-workflow/scripts/audit.py deps add 007 --depends-on 003
```

## Graph

```text
003 (base Lock implementation)
├── 001 (session uses Lock) — depends on 003
└── 007 (cache uses Lock) — depends on 003
```

## Notes

{rationale, open questions, dependency risks}
