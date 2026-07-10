# Changelog

## 1.0.1

- Made `docs/CONTRACT.md` the single canonical behavioral contract and reduced `docs/PROTOCOL.md` to an operator quick reference to avoid duplicated status, actor, transition, evidence, field, and dependency tables.
- Documented verification-field backward compatibility: parsers may read legacy `Status`, `Date`, and `Commit Verified At`, but new writes use canonical verification fields.
- Documented `audit doctor --fix` semantics: fixes must be followed by a fresh health check before reporting the final result.
- Normalized MCP `audit_doctor` output to a structured JSON object, including parsed text output and a post-fix re-check result when `fix=true`.
- Made the MCP `audit_create` cold-start side effect explicit and returned both initialization and create results; initialization failure now stops ticket creation.
- Broadened the audit guard's shell rewrite detection for audit Markdown files, including indirect pipeline/write paths such as `cat | sed | mv` patterns.
- Added `disallowedTools` to the `audit-resolution` agent so it matches the other lifecycle agents and records audit metadata only through the CLI/MCP runtime.
- Documented that `audit-triage` is intentionally not a lifecycle actor; triage commands update scheduling and dependency metadata only.
- Listed `docs/references/runtime-diagnosis-patterns.md` as a maintained operational reference that must stay aligned with runtime behavior.

## 1.0.0

- Packaged the audit workflow as a Claude Code plugin marketplace entry.
- Added four symmetric skills: `audit-discovery`, `audit-triage`, `audit-resolution`, `audit-verification`.
- Added four role agents.
- Added slash-command entrypoints for init, status, next, and each role.
- Added plugin hooks that block direct lifecycle status bypasses.
- Added a dependency-free MCP stdio server wrapping `bin/audit` JSON surfaces.
- Added self-contained `bin/audit` CLI fallback.
