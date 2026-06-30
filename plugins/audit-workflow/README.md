# Audit Workflow Plugin

Evidence-first governed audit workflow for Claude Code.

This is a full plugin bundle, not a skills-only pack. It includes:

```text
skills/      role procedures
agents/      role-isolated subagents
commands/    slash-command entrypoints
hooks/       lifecycle guardrails
mcp/         structured audit tools
bin/audit    portable CLI fallback
```

## Install from the local marketplace

From the directory that contains `artur-plugins/`:

```text
/plugin marketplace add ./artur-plugins
/plugin install audit-workflow@artur-plugins
```

Then reload plugins if needed:

```text
/reload-plugins
```

## First run in a project

```text
/audit-workflow:audit-init
/audit-workflow:audit-status
```

CLI fallback while the plugin is enabled:

```bash
audit init
audit doctor
audit summary
```

## Normal flows

```text
/audit-workflow:audit-discovery
/audit-workflow:audit-triage
/audit-workflow:audit-resolution
/audit-workflow:audit-verification
```

## Governance guarantees

- `audit/` tree is initialized by `audit init`, not invented by the model.
- Status changes go through CLI/MCP lifecycle commands.
- `audit-resolution` stops at `READY_FOR_VERIFICATION`.
- `audit-verification` is the normal role that writes `PASS`.
- Hooks block direct edits that try to bypass lifecycle status transitions.
- MCP tools expose structured automation surfaces; `bin/audit` remains the debug/fallback path.

## Runtime commands

```bash
audit next --for resolution --json
audit next --for verification --json
audit export --json
```

## Files

- `docs/CONTRACT.md` — lifecycle and role contract.
- `docs/PROTOCOL.md` — audit protocol details.
- `docs/references/` — templates and supporting references.
