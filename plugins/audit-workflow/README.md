# Audit Workflow Plugin

Evidence-first governed audit workflow for Claude Code. The package layout is compatible with claude.ai organization plugin sync.

```text
skills/      role procedures and read-only investigation
agents/      role-isolated subagents
commands/    init/status/next conveniences
hooks/       lifecycle guardrails
mcp/         structured audit tools
scripts/     canonical audit runtime plus read-only scattering scanner
```

There is deliberately no top-level `bin/`: claude.ai/Cowork organization marketplace sync rejects plugins that contain one.

## Install from the marketplace

```text
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/reload-plugins
```

## Review without creating audit state

```text
/audit-workflow:deep-review
/audit-workflow:feature-scattering
```

`deep-review` returns traceable confirmed defects, risks, and improvement suggestions.
It loads click-path, test-quality, and operator-surface references only for the
requested analysis. It does not initialize `audit/`, invoke the discovery agent,
edit code, or create tickets unless separately authorized. `feature-scattering`
uses the bundled Python 3.10+ scanner with explicit scope and coverage; Git history
is optional and unavailable history is not reported as zero co-change.

Resolution and verification share [resolution proof](docs/references/resolution-proof.md),
separating proposed checks, observed outcomes, verdicts, and running-instance proof.
The existing runtime and lifecycle remain unchanged.

## Ticket lifecycle first run

```text
/audit-workflow:audit-init
/audit-workflow:audit-status
```

Prefer the structured `audit_*` MCP tools. CLI fallback inside Claude plugin content:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" summary
```

From a repository clone, use:

```bash
python3 plugins/audit-workflow/scripts/audit.py <command> [options]
```

## Normal flows

```text
/audit-workflow:audit-discovery
/audit-workflow:audit-triage
/audit-workflow:audit-resolution
/audit-workflow:audit-verification
```

## Governance guarantees

- audit state is initialized through MCP/CLI rather than invented by the model;
- lifecycle status changes go through the guarded runtime;
- `audit-resolution` may edit implementation code but stops at `READY_FOR_VERIFICATION`;
- `audit-verification` owns independent verdicts and `PASS` requires explicit `ACn: pass` results;
- hooks reject direct audit lifecycle rewrites through Edit/Write and shell mutation paths;
- dependency mutations update both `Depends On` and `Blocks` sides;
- MCP covers the normal lifecycle including show, open, triage, and dependency add/remove.

## Platform scope

The runtime currently requires a `python3` executable. The target host platform is macOS/Linux Claude Code. Installed plugin skills are also available in Chat; the Cowork runtime for the `python3` hooks and the stdio MCP server has not been verified. Native Windows Claude Code is intentionally not advertised as supported yet; the PowerShell mutation matcher is present, but the Python launcher remains POSIX-oriented.

## Files

- `docs/CONTRACT.md` — canonical lifecycle and role contract.
- `docs/PROTOCOL.md` — operator quick reference.
- `docs/references/` — durable audit templates/references.
- `scripts/audit.py` — canonical runtime and direct CLI fallback.
