# claude-plugins

Plugin marketplace for governed audit workflows and portable architecture skills.

## Install

From a clone of this repository:

```text
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/plugin install system-architect@artur-plugins
/reload-plugins
```

From GitHub:

```text
git clone https://github.com/garbageek/claude-plugins
cd claude-plugins
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/plugin install system-architect@artur-plugins
/reload-plugins
```

## Plugins

### audit-workflow

Evidence-first audit workflow with:

- role procedures in `skills/`
- role-isolated agents in `agents/`
- slash-command entrypoints in `commands/`
- lifecycle guardrails in `hooks/`
- structured MCP tools in `mcp/`
- portable CLI fallback in `bin/audit`

See [plugins/audit-workflow/README.md](plugins/audit-workflow/README.md).

### system-architect

Implementation-ready architecture SPECs, architecture reviews, and design decisions.
Invoke `/system-architect:architect` in Claude Code.

The complete portable package lives in `plugins/system-architect/`: canonical
`plugin.json`, OpenAI/Codex compatibility metadata, Claude manifest, branding
assets, and the architect skill with its templates and references. The imported
0.9.6 package is preserved byte-for-byte. Both plugins use the documented Claude
`displayName` field. Claude Code 2.1.141 rejects this field and does not support
`plugin validate --strict`; its validation results do not establish compatibility
with the current documented manifest schema.

## Validate

GitHub Actions validates every marketplace plugin: JSON/YAML, skill metadata,
package links, manifest identity/version consistency, OpenAI interface parity,
and referenced PNG icon dimensions and sizes. Existing audit runtime syntax
and layout checks remain in place.

Local validation:

```bash
claude plugin validate .
claude plugin validate plugins/audit-workflow
claude plugin validate plugins/system-architect
python3 -m pip install PyYAML==6.0.3
python3 scripts/validate_plugins.py
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool plugins/audit-workflow/.claude-plugin/plugin.json >/dev/null
python3 -m json.tool plugins/audit-workflow/.mcp.json >/dev/null
python3 -m json.tool plugins/audit-workflow/hooks/hooks.json >/dev/null
python3 -m py_compile \
  plugins/audit-workflow/bin/audit \
  plugins/audit-workflow/hooks/audit_guard.py \
  plugins/audit-workflow/hooks/plugin_root.py \
  plugins/audit-workflow/mcp/audit_mcp_server.py \
  plugins/audit-workflow/scripts/audit_lib.py \
  plugins/audit-workflow/scripts/generate_summary.py \
  plugins/audit-workflow/scripts/generate_verification_report.py
```
