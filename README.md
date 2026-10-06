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

## Plugins

### audit-workflow

Evidence-first audit workflow with role skills/agents, lifecycle hooks, structured MCP tools, and a Python CLI fallback at `plugins/audit-workflow/scripts/audit.py`.

The plugin intentionally has no top-level `bin/` directory so it can pass claude.ai/Cowork organization marketplace sync. The runtime currently requires Python 3 as `python3`; The target host platform is macOS/Linux Claude Code. The package removes the top-level `bin/` sync blocker, but hosted sync acceptance remains unverified. Installed plugin skills are also available in Chat; the Cowork runtime for the `python3` hooks and the stdio MCP server has not been verified. Native Windows Claude Code is not claimed as supported until the Python launcher is made host-configurable.

See [plugins/audit-workflow/README.md](plugins/audit-workflow/README.md).

### system-architect

Implementation-ready architecture SPECs, architecture reviews, and design decisions. Invoke `/system-architect:architect` in Claude Code.

The portable package lives in `plugins/system-architect/`: canonical `plugin.json`, OpenAI/Codex compatibility metadata, Claude manifest, branding assets, and the architect skill with its templates and references.

## Validate

GitHub Actions validates the Claude marketplace, the OpenAI/Codex repo marketplace, plugin JSON/YAML/frontmatter, local package links, manifest identity/version consistency, OpenAI interface parity, PNG assets, and the audit Python entrypoints.

Local validation:

```bash
claude plugin validate --strict plugins/audit-workflow
claude plugin validate --strict plugins/system-architect
python3 -m pip install PyYAML==6.0.3
python3 scripts/validate_plugins.py
python3 -m py_compile \
  plugins/audit-workflow/scripts/audit.py \
  plugins/audit-workflow/hooks/audit_guard.py \
  plugins/audit-workflow/hooks/plugin_root.py \
  plugins/audit-workflow/mcp/audit_mcp_server.py
```

Current vendor documentation:

- Claude plugins: https://code.claude.com/docs/en/plugins-reference
- OpenAI plugins: https://developers.openai.com/plugins/build/plugins
