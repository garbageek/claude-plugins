# Changelog

## 1.0.0

- Packaged the audit workflow as a Claude Code plugin marketplace entry.
- Added four symmetric skills: `audit-discovery`, `audit-triage`, `audit-resolution`, `audit-verification`.
- Added four role agents.
- Added slash-command entrypoints for init, status, next, and each role.
- Added plugin hooks that block direct lifecycle status bypasses.
- Added a dependency-free MCP stdio server wrapping `bin/audit` JSON surfaces.
- Added self-contained `bin/audit` CLI fallback.
