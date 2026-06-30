# claude-plugins

Local Claude Code plugin marketplace for governed agent workflows.

## Install

From a clone of this repository:

```text
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/reload-plugins
```

From GitHub:

```text
git clone https://github.com/garbageek/claude-plugins
cd claude-plugins
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
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

## Validate

The repository includes a GitHub Actions validator for JSON parsing, Python
syntax, Markdown frontmatter shape, and default plugin layout checks.

Local validation:

```bash
claude plugin validate --strict .
claude plugin validate --strict plugins/audit-workflow
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
