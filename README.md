# claude-plugins

Plugin marketplace for evidence-led audit, architecture, prompt design, human runbooks, source-backed codebase documentation, and repository instructions.

## Install

### Claude Code

```text
/plugin marketplace add garbageek/claude-plugins
/plugin install <plugin>@artur-plugins
/reload-plugins
```

Available plugins:

```text
audit-workflow
system-architect
prompt-design
human-runbooks
codebase-docs
repo-instructions
```

### OpenAI Codex

```bash
codex plugin marketplace add garbageek/claude-plugins
codex plugin add <plugin>@artur-plugins
```

The Codex marketplace contains:

```text
system-architect
prompt-design
human-runbooks
codebase-docs
repo-instructions
```

`audit-workflow` is intentionally Claude-only because its lifecycle integration uses Claude-specific hooks, agents, commands, and a local MCP/Python runtime.

## Plugins

### audit-workflow

Evidence-first audit lifecycle with discovery, triage, resolution, independent verification, read-only deep review, feature-scattering analysis, lifecycle hooks, MCP tools, and the canonical Python runtime at `plugins/audit-workflow/scripts/audit.py`.

Main entry points:

```text
/audit-workflow:deep-review
/audit-workflow:feature-scattering
/audit-workflow:audit-discovery
/audit-workflow:audit-triage
/audit-workflow:audit-resolution
/audit-workflow:audit-verification
```

Requires `python3`; the feature-scattering helper requires Python 3.10+. The supported full-runtime Claude Code target is macOS/Linux. Native Windows and the full Cowork runtime are not claimed as supported/verified.

See [plugins/audit-workflow/README.md](plugins/audit-workflow/README.md).

### system-architect

Implementation-ready architecture SPECs, reviews, design decisions, optional implementation-planning profiles, and evidence-based damaged-project recovery.

```text
/system-architect:architect
/system-architect:recover
```

Portable across the Claude and OpenAI/Codex marketplaces.

### prompt-design

Creates, rewrites, diagnoses, adapts, and evaluates prompts, including source-backed translation from implemented service behavior.

```text
/prompt-design:design-prompts
```

Portable across the Claude and OpenAI/Codex marketplaces.

### human-runbooks

Drafts, updates, and resumes human-executed procedures with explicit actions, observations, retry decisions, and final validation.

```text
/human-runbooks:human-execution-runbook
```

Portable across the Claude and OpenAI/Codex marketplaces.

### codebase-docs

Documents implemented systems through source-backed PRDs and local repository wikis.

```text
/codebase-docs:code-to-prd
/codebase-docs:local-wiki
```

Bundled helpers require Python 3.10+. Optional HTML wiki rendering additionally uses the dependencies listed in the local-wiki skill.

Portable package metadata is published for Claude and OpenAI/Codex; helper-backed workflows require local repository access and Python execution.

### repo-instructions

Creates and reviews repository-scoped Claude/Codex instructions from actual commands, boundaries, and existing guidance.

```text
/repo-instructions:init
/repo-instructions:review
```

Portable across the Claude and OpenAI/Codex marketplaces.

## Marketplace layout

```text
.claude-plugin/marketplace.json
    audit-workflow
    system-architect
    prompt-design
    human-runbooks
    codebase-docs
    repo-instructions

.agents/plugins/marketplace.json
    system-architect
    prompt-design
    human-runbooks
    codebase-docs
    repo-instructions
```

## Validate

GitHub Actions validates both marketplace registries, plugin metadata/frontmatter, local package links, manifest identity/version consistency, OpenAI interface/category consistency, repository layout, and maintained Python helpers.

Local validation:

```bash
python3 -m pip install PyYAML==6.0.3
python3 scripts/validate_plugins.py
python3 -m py_compile \
  plugins/audit-workflow/scripts/audit.py \
  plugins/audit-workflow/hooks/audit_guard.py \
  plugins/audit-workflow/hooks/plugin_root.py \
  plugins/audit-workflow/mcp/audit_mcp_server.py \
  plugins/audit-workflow/scripts/scatter_scan.py \
  plugins/codebase-docs/skills/code-to-prd/scripts/codebase_analyzer.py \
  plugins/codebase-docs/skills/code-to-prd/scripts/prd_scaffolder.py
python3 -m compileall -q plugins/codebase-docs/skills/local-wiki/scripts
```

## Documentation

- Claude Code plugin development: https://code.claude.com/docs/en/plugins/create
- Claude Code plugin installation and marketplaces: https://code.claude.com/docs/en/plugins/install
- Claude Code plugin manifest reference: https://code.claude.com/docs/en/plugins-reference
- OpenAI plugin packaging and repository marketplaces: https://developers.openai.com/plugins/build/plugins
