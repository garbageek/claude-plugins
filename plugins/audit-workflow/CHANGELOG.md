# Changelog

## 1.2.0

- Added read-only `deep-review` with click-path, existing-test-quality, and operator-surface lenses; ticketization remains an explicit canonical-runtime handoff.
- Added feature-scattering analysis with scoped static signals, bounded Git co-change, and explicit coverage/unavailable-history reporting.
- Added one shared resolution/verification proof guide, including activation and running-instance evidence.
- Preserved the lifecycle runtime, actors, commands, agents, hooks, MCP server, categories, and exports. This content expansion does not add Codex runtime support.

## 1.1.1

- `next`, `export` and `doctor` treat a dependency recorded on only one ticket (as 1.0.x `deps add N --blocks M` wrote it) as a full edge. `doctor` warns about such edges and `doctor --fix` writes the missing side.
- The audit guard again allows the bundled runtime (`python3 .../scripts/audit.py ...`) when its quoted arguments mention audit paths and status words, for example `--evidence "see audit/tickets/001-BUG-x.md"`. The check is per shell segment, so a direct rewrite chained after a runtime call, or a redirect of runtime output into an audit file, is still denied.
- Hook-launched `audit doctor` runs that exceed 12 seconds report a timeout instead of crashing the hook.
- The MCP server negotiates `2025-06-18` (the revision that defines `structuredContent`) and still accepts `2025-03-26`.
- The README no longer claims support on all hosted Claude surfaces: plugin skills are available in Chat, while hosted sync acceptance and the Cowork runtime for hooks and the stdio MCP server are unverified.

## 1.1.0

- Removed the top-level `bin/` directory and moved the canonical CLI/runtime to `scripts/audit.py` for claude.ai/Cowork marketplace compatibility.
- Collapsed duplicated CLI fallback constants, the `audit_lib` shim, the process-global `re.compile` monkeypatch, and the parity checker into one runtime source of truth.
- Fixed PASS gating so only explicit `ACn: pass` results satisfy acceptance criteria; non-pass criteria are stored unchecked.
- Closed chained shell-command lifecycle bypasses, allowed legitimate bundled CLI lifecycle calls without false positives, and added PowerShell mutation recognition.
- Canonicalized dependency IDs before self-reference checks so leading-zero aliases cannot create self-edges.
- Restored source editing capability to the `audit-resolution` agent.
- Made `doctor --fix` report and exit from a fresh post-fix diagnosis.
- Made dependency edges canonical and bidirectional for add/remove operations.
- Bounded Stop-hook feedback with `stop_hook_active` and shortened nested doctor timeout.
- Fixed MCP protocol negotiation so the server never claims unsupported client versions.
- Expanded MCP lifecycle coverage with show, open, triage, and dependency add/remove tools plus stricter schemas and structured results.
- Removed duplicate role command wrappers; skills remain the canonical role prompts.
- Silenced SessionStart when a project has no audit state.
- Aligned the plugin-local license with the repository MIT license.
- Removed unused report generators and vendored Claude documentation snapshots.
- Extended repository validation to the OpenAI/Codex marketplace.
- Declared current platform scope explicitly: Python-3 macOS/Linux + hosted Claude; native Windows Claude Code is not claimed yet.

## 1.0.1

- Made `docs/CONTRACT.md` the single canonical behavioral contract and reduced `docs/PROTOCOL.md` to an operator quick reference to avoid duplicated status, actor, transition, evidence, field, and dependency tables.
- Documented verification-field backward compatibility: parsers may read legacy `Status`, `Date`, and `Commit Verified At`, but new writes use canonical verification fields.
- Documented `audit doctor --fix` semantics: fixes must be followed by a fresh health check before reporting the final result.
- Normalized MCP `audit_doctor` output to a structured JSON object, including parsed text output and a post-fix re-check result when `fix=true`.
- Made the MCP `audit_create` cold-start side effect explicit and returned both initialization and create results; initialization failure now stops ticket creation.
- Broadened the audit guard's shell rewrite detection for audit Markdown files, including indirect pipeline/write paths such as `cat | sed | mv` patterns.
- Added `disallowedTools` to the `audit-resolution` agent so it matches the other lifecycle agents and records audit metadata only through the CLI/MCP runtime.
- Documented that `audit-triage` is intentionally not a lifecycle actor; triage commands update scheduling and dependency metadata only.
- Added `scripts/check_runtime_contract_parity.py` to detect drift between `scripts/audit_lib.py` and the single-file fallback constants embedded in `bin/audit`.
- Listed `docs/references/runtime-diagnosis-patterns.md` as a maintained operational reference that must stay aligned with runtime behavior.

## 1.0.0

- Packaged the audit workflow as a Claude Code plugin marketplace entry.
- Added four symmetric skills: `audit-discovery`, `audit-triage`, `audit-resolution`, `audit-verification`.
- Added four role agents.
- Added slash-command entrypoints for init, status, next, and each role.
- Added plugin hooks that block direct lifecycle status bypasses.
- Added a dependency-free MCP stdio server wrapping `bin/audit` JSON surfaces.
- Added self-contained `bin/audit` CLI fallback.
