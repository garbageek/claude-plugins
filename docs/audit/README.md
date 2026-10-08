# Audit Workflow

Evidence-first governed audit workflow for local Claude Code and Codex, using one Python runtime, shared skills, and a shared MCP server.

```text
skills/      role procedures, init/status/next, and read-only investigation
agents/      Claude role-isolated subagents
hooks/       Claude/Codex configurations and one shared guard
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
`garbageek/claude-plugins`. Codex plugin installation does not guarantee that
bundled hooks are registered: follow the procedure below before relying on
audit lifecycle guardrails.

Invoke the shared skills as `$deep-review`, `$feature-scattering`,
`$audit-discovery`, `$audit-triage`, `$audit-resolution`, or `$audit-verification`.
For init/status/next, use `$audit-init`, `$audit-status`, `$audit-next`, or the corresponding `audit_*` MCP tools. Supply an
absolute project `root` to every MCP call. CLI fallback requires explicit
installed-plugin and project paths, as defined in the
[invocation contract](CONTRACT.md#1-canonical-runtime-invocation).

Verification runs in a fresh native Codex subagent or another independent
session, not by changing the resolver's role label. No custom Codex agents,
user settings, or project instruction files are installed automatically.

### Codex hook activation

The toolkit uses `.codex-plugin/plugin.json` with explicit `hooks` and `mcpServers`
paths. There is no portable root manifest. This selects the native Codex path
that calls `load_plugin_hooks`, avoiding the AgentPlugin branch which currently
returns no hook sources. The handlers still run the same Python guard as Claude.
See the [loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs)
and [supported packaging](https://developers.openai.com/plugins/build/plugins).

After installing, open `/hooks` and confirm the toolkit's `PreToolUse` and
`PostToolUse` definitions are present. Review and trust them, then observe a
blocked direct status edit and an allowed evidence edit in a disposable project.
Verify post-tool diagnosis too. Re-check trust and the installed package after updates.
Do not register a second copy through project/user hooks when the plugin hooks run.

If the installed client still does not expose or invoke these handlers, report
that concrete host gap. Do not claim lifecycle protection from a manifest or
successful Python execution alone. A deliberate fallback may merge the existing
`hooks/codex.json` event groups into the host's supported project/user hooks,
replacing `${PLUGIN_ROOT}` with the actual installed absolute path and preserving
all unrelated handlers; do that only as requested setup, then verify it. Remove
only obsolete fallback handlers after native plugin loading is confirmed.

Hooks cover the recognized tool calls, not every external filesystem mutation.
The canonical `audit.py` remains the owner of lifecycle transitions and evidence gates.

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

From a repository clone, use:

```bash
python3 scripts/audit.py <command> [options]
```

## Normal flows

```text
/artur-plugins:audit-discovery
/artur-plugins:audit-triage
/artur-plugins:audit-resolution
/artur-plugins:audit-verification
```

## Lifecycle rules and enforcement boundary

- audit state is initialized through MCP/CLI rather than invented by the model;
- lifecycle status changes go through the guarded runtime;
- `audit-resolution` may edit implementation code but stops at `READY_FOR_VERIFICATION`;
- `audit-verification` owns independent verdicts and `PASS` requires explicit `ACn: pass` results;
- hooks reject covered direct audit lifecycle rewrites through Claude Edit/Write, Codex apply_patch, and recognized shell mutation paths; they are not a filesystem sandbox;
- dependency mutations update both `Depends On` and `Blocks` sides;
- MCP covers the normal lifecycle including show, open, triage, and dependency add/remove.

## Platform scope

The runtime requires `python3`; the local integration targets macOS/Linux Claude
Code and Codex. Codex selects `mcp/codex.json` and `hooks/codex.json` through
its native manifest; Claude uses `.mcp.json` and `hooks/hooks.json`. Verify hook
registration and trust in each installed host. Both invoke the same Python guard.
`Stop` reports health without starting another turn or changing audit state.

A successful package check or direct Python/MCP run does not establish an
installed Claude/Codex session's hook behavior or independent agent execution.
Verify skill discovery, MCP launch, trusted hooks, and role handoff in the target
host before relying on end-to-end parity. Skills can load on other surfaces,
but local Python hooks and stdio MCP need a local execution environment; no
hosted/Cowork or native Windows runtime parity is claimed. The PowerShell
matcher does not by itself make the `python3` launcher Windows-portable.

## Files

- `docs/audit/CONTRACT.md` — canonical lifecycle and role contract.
- `docs/audit/PROTOCOL.md` — operator quick reference.
- `docs/audit/references/` — durable audit templates/references.
- `scripts/audit.py` — canonical runtime and direct CLI fallback.
