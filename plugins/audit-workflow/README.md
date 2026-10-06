# Audit Workflow Plugin

Evidence-first governed audit workflow for Claude Code. The package layout is compatible with claude.ai organization plugin sync.

```text
skills/      role procedures
agents/      role-isolated subagents
commands/    init/status/next conveniences
hooks/       lifecycle guardrails
mcp/         structured audit tools
scripts/     canonical Python runtime and CLI fallback
```

There is deliberately no top-level `bin/`: claude.ai/Cowork organization marketplace sync rejects plugins that contain one.

## Install from the marketplace

```text
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/reload-plugins
```

## First run

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

- `docs/CONTRACT.md` â€” canonical lifecycle and role contract.
- `docs/PROTOCOL.md` â€” operator quick reference.
- `docs/references/` â€” durable audit templates/references.
- `scripts/audit.py` â€” canonical runtime and direct CLI fallback.
