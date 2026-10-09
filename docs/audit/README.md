# Audit Workflow

Evidence-first governed audit workflow for local Claude Code and Codex, using one Python runtime, shared skills, and a shared MCP server.

```text
skills/      role procedures, init/status/next, and read-only investigation
agents/      Claude role-isolated subagents
mcp/         structured audit tools
scripts/     canonical audit runtime plus read-only scattering scanner
```

There is deliberately no top-level `bin/`: claude.ai/Cowork organization marketplace sync rejects plugins that contain one.

## Install from the marketplace

```text
/plugin marketplace add .
/plugin install artur-plugins@artur-plugins
/reload-plugins
```

## Codex installation and use

```bash
codex plugin marketplace add garbageek/claude-plugins
codex plugin add artur-plugins@artur-plugins
```

For an unpacked local checkout, use its absolute path instead of
`garbageek/claude-plugins`. The plugin does not register lifecycle hooks.

Invoke the shared skills as `$deep-review`, `$feature-scattering`,
`$audit-discovery`, `$audit-triage`, `$audit-resolution`, or `$audit-verification`.
For init/status/next, use `$audit-init`, `$audit-status`, `$audit-next`, or the corresponding `audit_*` MCP tools. Supply an
absolute project `root` to every MCP call. CLI fallback requires explicit
installed-plugin and project paths, as defined in the
[invocation contract](CONTRACT.md#1-canonical-runtime-invocation).

Verification runs in a fresh native Codex subagent or another independent
session, not by changing the resolver's role label. No custom Codex agents,
user settings, or project instruction files are installed automatically.

Lifecycle transitions through MCP/CLI are validated by `audit.py`. Direct Markdown edits are not intercepted, and `audit doctor` is not invoked automatically. Use `audit_doctor` or the CLI `doctor` command to inspect existing state.

## Review without creating audit state

```text
/artur-plugins:deep-review
/artur-plugins:feature-scattering
```

`deep-review` returns traceable confirmed defects, risks, and improvement suggestions.
It loads click-path, test-quality, and operator-surface references only for the
requested analysis. It does not initialize `audit/`, invoke the discovery agent,
edit code, or create tickets unless separately authorized. `feature-scattering`
uses the bundled Python 3.10+ scanner with explicit scope and coverage; Git history
is optional and unavailable history is not reported as zero co-change.

Resolution and verification share [resolution proof](references/resolution-proof.md),
separating proposed checks, observed outcomes, verdicts, and running-instance proof.
The existing lifecycle, actors, and evidence gates are retained.

## Ticket lifecycle first run

```text
/artur-plugins:audit-init
/artur-plugins:audit-status
```

Prefer the structured `audit_*` MCP tools. For an ordinary Bash CLI fallback,
resolve the actual installed plugin and target project paths first:

```bash
export AUDIT_PLUGIN_ROOT="/absolute/installed/artur-plugins"
export AUDIT_PROJECT_DIR="/absolute/target/project"
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

Replace the placeholder paths; a normal shell need not export `CLAUDE_PLUGIN_ROOT`.

From the toolkit repository root, pass the selected external project explicitly:

```bash
python3 scripts/audit.py --root "/absolute/target/project" <command> [options]
```

For installation, upgrades, source selection or stale installed copies, use
[install-agent-plugins](../../skills/install-agent-plugins/SKILL.md), not the audit
state initializer.

## Normal flows

```text
/artur-plugins:audit-discovery
/artur-plugins:audit-triage
/artur-plugins:audit-resolution
/artur-plugins:audit-verification
```

## Lifecycle rules and enforcement boundary

- audit state is initialized through MCP/CLI rather than invented by the model;
- lifecycle transitions submitted through MCP/CLI are checked by the runtime; direct Markdown edits are not intercepted;
- `audit-resolution` may edit implementation code but stops at `READY_FOR_VERIFICATION`;
- `audit-verification` owns independent verdicts and `PASS` requires explicit `ACn: pass` results;
- dependency mutations update both `Depends On` and `Blocks` sides;
- MCP covers the normal lifecycle including show, open, triage, and dependency add/remove.

## Platform scope

The runtime requires `python3`; the local integration targets macOS/Linux Claude Code and Codex. Codex selects `mcp/codex.json` through its native manifest; Claude uses `.mcp.json`. There are no bundled lifecycle hooks. Verify installed skill discovery, MCP launch, and independent role handoff in the target host; package validation alone does not prove runtime behavior. Hosted/Cowork and native Windows runtime parity remain unverified.

## Files

- `docs/audit/CONTRACT.md` — canonical lifecycle and role contract.
- `docs/audit/PROTOCOL.md` — operator quick reference.
- `docs/audit/references/` — durable audit templates/references.
- `scripts/audit.py` — canonical runtime and direct CLI fallback.
