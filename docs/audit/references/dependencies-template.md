# Ticket Dependencies

Optional human-readable projection of ticket dependencies. This file is not
consumed by the CLI. Use `deps add/remove` to write both ticket headers first.

## Edges (machine-readable)

```text
# format: <blocking-ticket> blocks <blocked-ticket>
# Summarize the real edges already recorded in ticket headers.
003 blocks 001
003 blocks 007
```

Meaning: `001` and `007` depend on `003`. These lines document existing ticket
metadata, but do not create dependencies themselves.

Equivalent CLI form:

```bash
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" deps add 001 --depends-on 003
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" deps add 007 --depends-on 003
```

## Graph

```text
003 (base Lock implementation)
├── 001 (session uses Lock) — depends on 003
└── 007 (cache uses Lock) — depends on 003
```

## Notes

{rationale, open questions, dependency risks}
