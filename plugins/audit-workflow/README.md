# Audit Workflow Plugin

Evidence-first governed audit workflow for local Claude Code and Codex, using one Python runtime, shared skills, and a shared MCP server.

```text
skills/      role procedures and read-only investigation
agents/      Claude role-isolated subagents
commands/    Claude init/status/next conveniences; Codex uses MCP
hooks/       Claude/Codex configurations and one shared guard
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

## Codex installation and use

```bash
codex plugin marketplace add garbageek/claude-plugins
codex plugin add audit-workflow@artur-plugins
```

For an unpacked local checkout, use its absolute path instead of
`garbageek/claude-plugins`. Codex plugin installation does not guarantee that
bundled hooks are registered: follow the procedure below before relying on
audit lifecycle guardrails.

Invoke the shared skills as `$deep-review`, `$feature-scattering`,
`$audit-discovery`, `$audit-triage`, `$audit-resolution`, or `$audit-verification`.
For init/status/next, use the corresponding `audit_*` MCP tools. Supply an
absolute project `root` to every MCP call. CLI fallback requires explicit
installed-plugin and project paths, as defined in the
[invocation contract](docs/CONTRACT.md#1-canonical-runtime-invocation).

Verification runs in a fresh native Codex subagent or another independent
session, not by changing the resolver's role label. No custom Codex agents,
user settings, or project instruction files are installed automatically.

### Codex hook activation

**Verify hook discovery; do not infer it from plugin installation.** The portable
manifest points at `hooks/codex.json`, as described by [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins).
However, the inspected [Codex AgentPlugin loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs)
returns no hook sources for that manifest format. A different installed version
may behave differently. This is an upstream limitation, not a missing audit
Python handler.

1. Open `/hooks` after installation. If the plugin's `PreToolUse` and `PostToolUse`
   hooks are present, review and trust their exact definitions.
2. If they are absent, resolve the **actual installed** `audit-workflow` directory
   containing `hooks/audit_guard.py`. For a trusted target project, copy the
   existing `hooks/codex.json` into `<project>/.codex/hooks.json` (or merge its
   event groups into an existing hook file; **never overwrite existing hooks**).
   Replace every `${PLUGIN_ROOT}` in the copied commands with that installed
   directory's absolute path. Do not assume the plugin-only environment variable
   is available to project/user hook definitions.
3. Restart the local Codex session. Open `/hooks`, review and trust those hooks,
   then verify the real `PreToolUse` blocks a direct managed audit-ticket status
   edit and still permits an ordinary evidence edit. Re-check the paths and trust
   status after updating or reinstalling the plugin.

This is an opt-in project/user hook configuration supported by Codex, **not an
automatic portable-plugin fix**. If the hooks cannot be confirmed running,
treat the Codex plugin as skills/MCP-capable but do **not** claim guarded audit
state or full Claude/Codex lifecycle parity. Hooks are defense in depth and do
not replace filesystem permissions or the canonical `audit.py` state machine.

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

Prefer the structured `audit_*` MCP tools. For an ordinary Bash CLI fallback,
resolve the actual installed plugin and target project paths first:

```bash
export AUDIT_PLUGIN_ROOT="/absolute/installed/audit-workflow"
export AUDIT_PROJECT_DIR="/absolute/target/project"
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

Replace the placeholder paths; a normal shell need not export `CLAUDE_PLUGIN_ROOT`.

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
- hooks reject covered direct audit lifecycle rewrites through Claude Edit/Write, Codex apply_patch, and recognized shell mutation paths; they are not a filesystem sandbox;
- dependency mutations update both `Depends On` and `Blocks` sides;
- MCP covers the normal lifecycle including show, open, triage, and dependency add/remove.

## Platform scope

The runtime requires `python3`; the local integration targets macOS/Linux Claude
Code and Codex. Codex uses `mcp.json` and declares `hooks/codex.json`; Claude
retains `.mcp.json` and `hooks/hooks.json`. Codex's current AgentPlugin loader
may skip the declared hooks; verify or activate hooks explicitly as described
above. Where hooks are loaded, both hosts invoke the same Python guard.
`Stop` reports health without starting another turn or changing audit state.

A successful package check or direct Python/MCP run does not establish an
installed Claude/Codex session's hook behavior or independent agent execution.
Verify skill discovery, MCP launch, trusted hooks, and role handoff in the target
host before relying on end-to-end parity. Skills can load on other surfaces,
but local Python hooks and stdio MCP need a local execution environment; no
hosted/Cowork or native Windows runtime parity is claimed. The PowerShell
matcher does not by itself make the `python3` launcher Windows-portable.

## Files

- `docs/CONTRACT.md` — canonical lifecycle and role contract.
- `docs/PROTOCOL.md` — operator quick reference.
- `docs/references/` — durable audit templates/references.
- `scripts/audit.py` — canonical runtime and direct CLI fallback.
