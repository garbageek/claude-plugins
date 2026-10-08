# claude-plugins

Plugin marketplace for evidence-led audit, architecture, prompts, prose editing, human procedures, source-backed documentation, repository/Copilot review instructions, Codex server operations, coding-session handovers, and cross-platform plugin authoring.

This README covers repository-specific installation, plugin usage, runtime notes, and validation.

## Plugin catalog

| Plugin | Claude marketplace | OpenAI/Codex marketplace | Entry skills | Runtime requirements |
|---|---|---|---|---|
| `audit-workflow` | yes | yes | `deep-review`, `feature-scattering`, existing audit lifecycle skills | `python3`; `feature-scattering` helper requires Python 3.10+ |
| `system-architect` | yes | yes | `architect`, `recover` | none beyond the host app |
| `prompt-design` | yes | yes | `design-prompts` | none beyond the host app |
| `human-runbooks` | yes | yes | `human-execution-runbook` | none beyond the host app |
| `codebase-docs` | yes | yes | `code-to-prd`, `local-wiki` | Python 3.10+ for helpers; optional HTML wiki rendering also uses skill-local Jinja2/markdown-it-py dependencies |
| `repo-instructions` | yes | yes | `init`, `review`, `copilot-review-customizer` | No bundled runtime; Copilot customization needs current GitHub docs and repository/history access or supplied source evidence |
| `humanizer` | yes | yes | `humanizer` | none beyond the host app |
| `codex-ubuntu-server` | yes | yes | `codex-ubuntu-server` | Target Ubuntu host, shell/SSH access, and Codex CLI for maintenance; no bundled local runtime |
| `uncompromising-handover` | yes | yes | `uncompromising-handover` | none beyond the host app; checkpoint delivery requires a writable/accessibly shared location |
| `artur-plugin-creator` | yes | yes | `create-plugin`, `inspect-plugin`, `update-plugin` | Source/file tools for authoring; Plugin Creator backend only for requested hosted operations |

Both marketplaces expose the same plugins listed above. `audit-workflow` includes a
local Python/MCP runtime and host-specific hook configurations; Codex hooks must
be reviewed and trusted before they run. Repository validation is not proof of
installed-host behavior.

---

# 1. Claude Code

## 1.1 Install from GitHub

Register the GitHub marketplace once.

Inside a Claude Code session:

```text
/plugin marketplace add garbageek/claude-plugins
```

Or from the shell:

```bash
claude plugin marketplace add garbageek/claude-plugins
```

Install only the plugins you need:

```text
/plugin install audit-workflow@artur-plugins
/plugin install system-architect@artur-plugins
/plugin install prompt-design@artur-plugins
/plugin install human-runbooks@artur-plugins
/plugin install codebase-docs@artur-plugins
/plugin install repo-instructions@artur-plugins
/plugin install humanizer@artur-plugins
/plugin install codex-ubuntu-server@artur-plugins
/plugin install uncompromising-handover@artur-plugins
/plugin install artur-plugin-creator@artur-plugins
```

Shell equivalents:

```bash
claude plugin install audit-workflow@artur-plugins
claude plugin install system-architect@artur-plugins
claude plugin install prompt-design@artur-plugins
claude plugin install human-runbooks@artur-plugins
claude plugin install codebase-docs@artur-plugins
claude plugin install repo-instructions@artur-plugins
claude plugin install humanizer@artur-plugins
claude plugin install codex-ubuntu-server@artur-plugins
claude plugin install uncompromising-handover@artur-plugins
claude plugin install artur-plugin-creator@artur-plugins
```

Each interactive `/plugin install ...` opens plugin details first so you can review the package and choose the installation scope.

## 1.2 Choose the Claude install scope

| Scope | Meaning | Settings file |
|---|---|---|
| `user` | Available to you in every project on this machine | `~/.claude/settings.json` |
| `project` | Enabled for collaborators in this repository | `.claude/settings.json` |
| `local` | Enabled only for you in this repository | `.claude/settings.local.json` |

Example:

```bash
claude plugin install prompt-design@artur-plugins --scope user
claude plugin install prompt-design@artur-plugins --scope project
claude plugin install prompt-design@artur-plugins --scope local
```

`user` is the default shell scope. If the same plugin is configured at several scopes, precedence is:

```text
local > project > user
```

A committed project setting enables the plugin for collaborators but does not download the plugin package for them. Each collaborator still installs the plugin once at project scope.

## 1.3 Apply and verify

A plugin installed from the shell is available on the next Claude Code start. In an already open session:

```text
/reload-plugins
```

If Claude warns that reloading would invalidate the prompt cache:

```text
/reload-plugins --force
```

List installed plugins:

```bash
claude plugin list
```

Inspect individual plugins:

```bash
claude plugin details audit-workflow
claude plugin details system-architect
claude plugin details prompt-design
claude plugin details human-runbooks
claude plugin details codebase-docs
claude plugin details repo-instructions
claude plugin details humanizer
claude plugin details codex-ubuntu-server
claude plugin details uncompromising-handover
claude plugin details artur-plugin-creator
```

### Skill entry points

| Plugin | Claude Code entry points |
|---|---|
| `audit-workflow` | `/audit-workflow:deep-review`, `/audit-workflow:feature-scattering`, lifecycle skills listed below |
| `system-architect` | `/system-architect:architect`, `/system-architect:recover` |
| `prompt-design` | `/prompt-design:design-prompts` |
| `human-runbooks` | `/human-runbooks:human-execution-runbook` |
| `codebase-docs` | `/codebase-docs:code-to-prd`, `/codebase-docs:local-wiki` |
| `repo-instructions` | `/repo-instructions:init`, `/repo-instructions:review`, `/repo-instructions:copilot-review-customizer` |
| `humanizer` | `/humanizer:humanizer` |
| `codex-ubuntu-server` | `/codex-ubuntu-server:codex-ubuntu-server` |
| `uncompromising-handover` | `/uncompromising-handover:uncompromising-handover` |
| `artur-plugin-creator` | `/artur-plugin-creator:create-plugin`, `/artur-plugin-creator:inspect-plugin`, `/artur-plugin-creator:update-plugin` |

### `audit-workflow`
Read-only investigation can now start without creating audit state:

```text
/audit-workflow:deep-review
/audit-workflow:feature-scattering
```

`deep-review` checks the reported path, affected consumers, and independent failure possibilities within the requested scope. It preserves product intent, distinguishes unfamiliar mechanisms from unnecessary ones, and can route to click-path, test-quality, and operator-surface analysis when relevant. `feature-scattering` uses its bundled scanner but does not create tickets by default.

Ticket-lifecycle first run remains:

```text
/audit-workflow:audit-init
/audit-workflow:audit-status
```

Normal lifecycle flows remain:

```text
/audit-workflow:audit-discovery
/audit-workflow:audit-triage
/audit-workflow:audit-resolution
/audit-workflow:audit-verification
```

The canonical Python CLI fallback is unchanged:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" init
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" doctor
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit.py" summary
```

From a repository clone:

```bash
python3 plugins/audit-workflow/scripts/audit.py <command> [options]
```

### `system-architect`
Use the canonical architecture workflow for normal architecture work:

```text
/system-architect:architect
```

The architect now includes optional epic, milestone, and roadmap output profiles plus focused CLI-contract guidance. Damaged-project assessment/recovery is a separate entry point:

```text
/system-architect:recover
```

Recovery assessment is read-only by default; recovery actions require explicit authorization.

### `prompt-design`
```text
/prompt-design:design-prompts
```

Supports prompt creation, rewrite, diagnosis, adaptation, evaluation, and source-backed service-to-prompt translation.

### `human-runbooks`
```text
/human-runbooks:human-execution-runbook
```

Supports drafting, updating from actual execution evidence, and resuming interrupted human-executed procedures. Small procedures remain compact. Staged procedures define entry conditions, durable exits, and re-entry evidence; a final consistency check covers the affected sequence without claiming the human performed it.

### `codebase-docs`
```text
/codebase-docs:code-to-prd
/codebase-docs:local-wiki
```

`code-to-prd` separates analysis/inventory from PRD scaffolding. Its helpers require Python 3.10+ and refuse destructive scaffolding into a populated destination.

`local-wiki` supports Markdown wiki finalization, validation, Markdown bundle export, and optional offline HTML output. Markdown operations use the standard library. HTML rendering additionally uses the skill-local `Jinja2` and `markdown-it-py` dependency list and should only install those dependencies when authorized.

### `repo-instructions`
```text
/repo-instructions:init
/repo-instructions:review
/repo-instructions:copilot-review-customizer
```

`init` creates instructions only for the requested host/scope. `review` is read-only by default and checks actual repository evidence plus current Claude/Codex instruction-loading behavior.

[copilot-review-customizer](plugins/repo-instructions/skills/copilot-review-customizer/SKILL.md) researches a concrete repository, mines usable review/regression history, and chooses the minimum Copilot Code Review customization. It supports analysis, complete files with placement paths, or an explicitly requested PR. Its contract ledger and three local references remain part of the workflow. Live GitHub documentation must confirm any mechanism it relies on; the mechanics reference is a starting point, not a reason to skip verification.

Installing `repo-instructions` supplies the **customizer**, not a review skill already installed in another repository. The customizer may produce `.github/skills/code-review/SKILL.md` in the selected project, update another appropriate surface, or conclude no change is needed. It needs documentation access and repository/history evidence; it prefers a GitHub connector and requests archives, a checkout, or command output when that access is unavailable. No GitHub connection, credentials, settings changes, or automatic reviews are provisioned by this package. Preparing files and confirming documented loading do not prove Copilot used them or improved a real review.

### `humanizer`
```text
/humanizer:humanizer
```

[humanizer](plugins/humanizer/skills/humanizer/SKILL.md) detects, rewrites, or edits formulaic prose when writing quality is requested. It handles technical documentation, PR descriptions, review comments, messages, and other prose while preserving meaning, certainty, code, identifiers, numbers, citations, and the sender's authority and commitments. Detect mode does not rewrite; already-clear text may remain unchanged. This is prose editing, not prompt design, an authorship detector, or an automatic filter on unrelated answers.

### `codex-ubuntu-server`

Use `/codex-ubuntu-server:codex-ubuntu-server` to administer Codex CLI on a selected Ubuntu host. The skill requires access to that host and does not authorize installation, updates, remote control, or service changes without the relevant request. It contains setup and maintenance references.

### `uncompromising-handover`

Use `/uncompromising-handover:uncompromising-handover` to create a self-contained continuation checkpoint for an active coding task. The bundled template is the source of the output format; checkpoint files are versioned and must not be committed automatically.

### `artur-plugin-creator`

[Artur Plugin Creator](plugins/artur-plugin-creator/skills/create-plugin/SKILL.md)
creates, inspects, and updates plugins for Claude Code, Codex, or both. A dual package
uses root `plugin.json`, `.claude-plugin/plugin.json`, and shared skills; required
MCP, hooks, or agents need real host adapters rather than a compatibility label.
Local repository/archive work does not require the Plugin Creator backend.

Use `create-plugin` for a new package, `inspect-plugin` for read-only inspection,
and `update-plugin` for changes or conversion. Hosted publication is optional and
requires the separately connected backend. Updates use release guards and explicit
`delete_paths`; omitting a file from an upload is not deletion. Preparing an archive
does not publish to a Claude account, an OpenAI account, GitHub, or a public directory.

## 1.4 Enable or disable

Use the same command for any plugin:

```bash
claude plugin disable <plugin>@artur-plugins
claude plugin enable <plugin>@artur-plugins
```

For example:

```bash
claude plugin disable codebase-docs@artur-plugins
claude plugin enable codebase-docs@artur-plugins
```

You can also use `/plugin` -> **Installed** and press **Space** on a plugin.

## 1.5 Update

Refresh only the marketplace listing:

```bash
claude plugin marketplace update artur-plugins
```

Update an installed plugin:

```bash
claude plugin update <plugin>@artur-plugins
```

Examples for the two upgraded existing products:

```bash
claude plugin update audit-workflow@artur-plugins
claude plugin update system-architect@artur-plugins
```

These operations are different:

```text
marketplace update -> refreshes marketplace metadata/listing
plugin update      -> updates one installed plugin
```

To refresh the marketplace and update all plugins installed from it in one operation, open `/plugin` -> **Marketplaces** -> `artur-plugins` -> **Update marketplace**.

Third-party marketplaces have auto-update disabled by default. Enable it from `/plugin` -> **Marketplaces** -> `artur-plugins` -> **Enable auto-update** if desired.

The current session keeps the plugin version already loaded until you run `/reload-plugins` or start a new session.

## 1.6 Upgrade from the previous two-plugin repository version


```bash
claude plugin marketplace update artur-plugins
claude plugin update audit-workflow@artur-plugins
claude plugin update system-architect@artur-plugins
```

Then install whichever new products you want:

```bash
claude plugin install prompt-design@artur-plugins
claude plugin install human-runbooks@artur-plugins
claude plugin install codebase-docs@artur-plugins
claude plugin install repo-instructions@artur-plugins
claude plugin install humanizer@artur-plugins
claude plugin install artur-plugin-creator@artur-plugins
```

Apply the updated plugins to an already open session with:

```text
/reload-plugins
```

## 1.7 Remove

Remove an individual plugin:

```bash
claude plugin uninstall <plugin>@artur-plugins
```

For example:

```bash
claude plugin uninstall prompt-design@artur-plugins
```

Remove the marketplace itself only when you no longer need any plugin from it:

```bash
claude plugin marketplace remove artur-plugins
```

Removing a Claude marketplace also uninstalls plugins installed from that marketplace and removes their enabled entries from Claude settings.

## 1.8 Desktop Code tab and VS Code

### Claude desktop app: local or SSH Code session

Open:

```text
+ -> Plugins -> Add plugin
```

Manage installed plugins with:

```text
+ -> Plugins -> Manage plugins
```

The plugin browser is not available in Claude Code cloud sessions.

### VS Code

Type:

```text
/plugins
```

Use the **Plugins** and **Marketplaces** tabs. Changes apply to open sessions without restarting VS Code.

---

# 2. Claude app, claude.ai, and Cowork

Open:

```text
Customize -> Plugins -> Add -> Add marketplace
```

Add either:

```text
garbageek/claude-plugins
```

or:

```text
https://github.com/garbageek/claude-plugins
```

The `artur-plugins` Claude marketplace exposes the packages listed in the [plugin catalog](#plugin-catalog).

The repository does not contain prebuilt per-plugin `.plugin` release archives, so the repository-marketplace path is the canonical installation path documented here.

## 2.1 Account sync to Claude Code

A plugin installed on your Claude account can sync down to Claude Code when Claude Code starts while signed in to the same account. It appears with an ID such as:

```text
<plugin>@synced
```

The reverse does not happen automatically: a plugin installed only with `/plugin` or `claude plugin install` remains on that machine and is not added to your Claude account.

## 2.2 Surface differences

### Skill-focused portable plugins

`system-architect`, `prompt-design`, `human-runbooks`, `repo-instructions`, `humanizer`, `uncompromising-handover`, and `artur-plugin-creator` are primarily skill/reference packages with no local runtime dependency. Their package shape is intended for Claude Code, Chat, and Cowork skill loading. Treat package structure and repository validation separately from proven execution parity on every Claude surface.

### `codebase-docs`

The skills can load as plugin content, but its practical repository-analysis workflows use local Python helpers and local source files. Full helper-backed behavior therefore depends on a host that can access the repository and run Python 3.10+. Optional HTML wiki rendering has additional skill-local Python dependencies.

### `audit-workflow`

`audit-workflow` contains skills, commands, agents, hooks, a local stdio MCP server, and a Python runtime:

- **Claude Code:** full intended target; skills, commands, agents, hooks, MCP tools, and Python runtime are packaged together.
- **Claude Chat:** skill/command content can load, while agents, hooks, and the local MCP runtime do not provide the same lifecycle runtime.
- **Cowork:** agents, hooks, and a local MCP server can load when the session runs on your computer, but this repository does not claim the `audit-workflow` Cowork runtime as verified; `python3` is required there.

The plugin deliberately has no top-level `bin/` directory because Claude Chat/Cowork installation rejects plugins that contain one.

---

# 3. OpenAI Codex

The native repository marketplace is:

```text
.agents/plugins/marketplace.json
```

It exposes the same catalog listed above, including `audit-workflow` for local
Codex sessions with Python and trusted hooks.

## 3.1 Install from GitHub

Register the GitHub marketplace:

```bash
codex plugin marketplace add garbageek/claude-plugins
```

Verify the source:

```bash
codex plugin marketplace list
```

Install the plugins you need:

```bash
codex plugin add audit-workflow@artur-plugins
codex plugin add system-architect@artur-plugins
codex plugin add prompt-design@artur-plugins
codex plugin add human-runbooks@artur-plugins
codex plugin add codebase-docs@artur-plugins
codex plugin add repo-instructions@artur-plugins
codex plugin add humanizer@artur-plugins
codex plugin add codex-ubuntu-server@artur-plugins
codex plugin add uncompromising-handover@artur-plugins
codex plugin add artur-plugin-creator@artur-plugins
```

Equivalent explicit marketplace form for any one plugin:

```bash
codex plugin add prompt-design --marketplace artur-plugins
```

or:

```bash
codex plugin add prompt-design -m artur-plugins
```

Verify installed and available plugins:

```bash
codex plugin list
codex plugin list --json
codex plugin list --marketplace artur-plugins --available --json
```

`--available` includes marketplace plugins that are not installed and requires `--json`.

Do not use `codex plugin install`; the documented Codex subcommand is `codex plugin add`.

## 3.2 Interactive installation and enablement

Start Codex and open:

```text
/plugins
```

Switch to the `artur-plugins` marketplace, open the desired plugin, and install it. Press **Space** on an installed plugin to enable or disable it.

In the ChatGPT desktop app, open the **Plugins** tab, select `artur-plugins`, and install the desired portable plugin.

Start a new chat or CLI session before first use so bundled skills and plugin content are loaded.

### Audit Workflow in Codex

After installing `audit-workflow`, open `/hooks` and review/trust its hook
configuration. Hooks that have not been trusted are skipped; installation alone
is insufficient. Use `$deep-review` or `$feature-scattering` for read-only work,
and `$audit-discovery`, `$audit-triage`, `$audit-resolution`, or
`$audit-verification` for the corresponding lifecycle role.

Pass the absolute project directory as `root` to every `audit_*` MCP call. The
portable MCP process starts from the installed package directory, so it refuses
a missing/relative root instead of creating audit state inside the plugin cache.
Claude retains its configured project-directory fallback.

The Claude init/status/next commands remain unchanged. In Codex, their operations
are available through `audit_init`, `audit_doctor`, `audit_summary`, and
`audit_next`; no generated command copies are needed. The shared verification
skill requires a fresh native subagent or another independent session, not a
resolver merely switching role names. See the
[audit invocation contract](plugins/audit-workflow/docs/CONTRACT.md#1-canonical-runtime-invocation)
for CLI path setup and host boundaries.

## 3.3 Refresh / upgrade the marketplace

Refresh this Git marketplace:

```bash
codex plugin marketplace upgrade artur-plugins
```

Without a marketplace name, Codex refreshes all configured Git marketplaces:

```bash
codex plugin marketplace upgrade
```

`upgrade` refreshes configured Git marketplace sources. It is separate from plugin installation state.

Machine-readable checks:

```bash
codex plugin marketplace list --json
codex plugin marketplace upgrade artur-plugins --json
codex plugin list --marketplace artur-plugins --available --json
```

### Upgrade from the previous repository version

Refresh the marketplace first:

```bash
codex plugin marketplace upgrade artur-plugins
codex plugin list --marketplace artur-plugins --available --json
```

Install additional portable products as needed:

```bash
codex plugin add prompt-design@artur-plugins
codex plugin add human-runbooks@artur-plugins
codex plugin add codebase-docs@artur-plugins
codex plugin add repo-instructions@artur-plugins
codex plugin add humanizer@artur-plugins
codex plugin add artur-plugin-creator@artur-plugins
```

There is no separate documented `codex plugin update` subcommand. If an already installed `system-architect` remains on the older cached version after marketplace refresh, remove and add it again:

```bash
codex plugin remove system-architect@artur-plugins
codex plugin add system-architect@artur-plugins
```

Then start a new Codex/ChatGPT desktop session.

## 3.4 Remove

Remove any installed portable plugin:

```bash
codex plugin remove <plugin>@artur-plugins
```

Equivalent explicit marketplace form:

```bash
codex plugin remove <plugin> --marketplace artur-plugins
```

`codex plugin remove` removes the installed plugin from local config and cache.

Remove the marketplace itself separately if it is no longer needed:

```bash
codex plugin marketplace remove artur-plugins
```

---

# 4. Work from a local clone

Clone the repository when developing plugins locally or when you want the marketplace to resolve directly from the working tree.

Clone and enter the repository:

```bash
git clone https://github.com/garbageek/claude-plugins.git
cd claude-plugins
```

The repository root contains:

```text
claude-plugins/
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json
└── plugins/
```

## 4.1 Claude Code local marketplace

Inside Claude Code from the repository root:

```text
/plugin marketplace add .
/plugin install audit-workflow@artur-plugins
/plugin install system-architect@artur-plugins
/plugin install prompt-design@artur-plugins
/plugin install human-runbooks@artur-plugins
/plugin install codebase-docs@artur-plugins
/plugin install repo-instructions@artur-plugins
/plugin install humanizer@artur-plugins
/plugin install codex-ubuntu-server@artur-plugins
/plugin install uncompromising-handover@artur-plugins
/plugin install artur-plugin-creator@artur-plugins
/reload-plugins
```

The Claude marketplace entries use relative plugin sources. When the marketplace is added from this local directory, Claude Code loads those plugins in place from the repository. Source edits become visible on the next session start or after `/reload-plugins`, without a version bump.

For one-session development of one plugin without installing the marketplace:

```bash
claude --plugin-dir ./plugins/audit-workflow
claude --plugin-dir ./plugins/system-architect
claude --plugin-dir ./plugins/prompt-design
claude --plugin-dir ./plugins/human-runbooks
claude --plugin-dir ./plugins/codebase-docs
claude --plugin-dir ./plugins/repo-instructions
claude --plugin-dir ./plugins/humanizer
claude --plugin-dir ./plugins/codex-ubuntu-server
claude --plugin-dir ./plugins/uncompromising-handover
claude --plugin-dir ./plugins/artur-plugin-creator
```

Use one `--plugin-dir` target per development session unless deliberately testing several plugin directories together.

## 4.2 Codex local marketplace

From the repository root:

```bash
codex plugin marketplace add .
codex plugin list --marketplace artur-plugins --available --json
```

Install selected portable plugins:

```bash
codex plugin add system-architect@artur-plugins
codex plugin add prompt-design@artur-plugins
codex plugin add human-runbooks@artur-plugins
codex plugin add codebase-docs@artur-plugins
codex plugin add repo-instructions@artur-plugins
codex plugin add humanizer@artur-plugins
codex plugin add codex-ubuntu-server@artur-plugins
codex plugin add uncompromising-handover@artur-plugins
codex plugin add artur-plugin-creator@artur-plugins
```

For local marketplace installs, the runtime copy is cached under:

```text
~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/
```

For a local plugin, the version directory is normally:

```text
local
```

Therefore during Codex development:

```text
source directory != installed runtime copy
```

If source changes are not reflected, refresh/reinstall the plugin and restart the relevant local client.

## 4.3 Repo-local Codex enablement

The repository marketplace makes the listed plugins discoverable. In a trusted clone, project-level enablement can be controlled through `.codex/config.toml`:

```toml
[plugins."audit-workflow@artur-plugins"]
enabled = true

[plugins."system-architect@artur-plugins"]
enabled = true

[plugins."prompt-design@artur-plugins"]
enabled = true

[plugins."human-runbooks@artur-plugins"]
enabled = true

[plugins."codebase-docs@artur-plugins"]
enabled = true

[plugins."repo-instructions@artur-plugins"]
enabled = true

[plugins."humanizer@artur-plugins"]
enabled = true

[plugins."codex-ubuntu-server@artur-plugins"]
enabled = true

[plugins."uncompromising-handover@artur-plugins"]
enabled = true

[plugins."artur-plugin-creator@artur-plugins"]
enabled = true
```

Set any entry to `false` to disable it for the project without uninstalling it.

Codex reads project `.codex/config.toml` only for trusted projects.

---

# 5. Why this repository has two marketplace manifests

`.claude-plugin/marketplace.json` uses Claude's catalog format;
`.agents/plugins/marketplace.json` uses the native OpenAI/Codex format. Both are
named `artur-plugins` and expose the same plugin set. They reference the same
plugin directories, not separate copies of the runtime or skills.

Use the native `.agents/plugins/marketplace.json` for Codex. Plugin-local
configuration selects the appropriate MCP and hooks integration for each host.

---

# 6. Repository layout relevant to installation

```text
.claude-plugin/
└── marketplace.json                  # Claude marketplace

.agents/plugins/
└── marketplace.json                  # OpenAI/Codex marketplace

plugins/
├── audit-workflow/
│   ├── plugin.json                   # portable metadata; selects hooks/codex.json
│   ├── mcp.json                      # portable stdio launcher; explicit project root
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json                     # Claude launcher
│   ├── skills/
│   │   ├── audit-discovery/
│   │   ├── audit-triage/
│   │   ├── audit-resolution/
│   │   ├── audit-verification/
│   │   ├── deep-review/
│   │   └── feature-scattering/
│   ├── agents/
│   ├── commands/
│   ├── hooks/
│   ├── mcp/
│   └── scripts/
│
├── system-architect/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   ├── .codex-plugin/plugin.json     # retained compatibility metadata
│   ├── assets/
│   └── skills/
│       ├── architect/
│       └── recover/
│
├── prompt-design/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   └── skills/design-prompts/
│
├── human-runbooks/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   └── skills/human-execution-runbook/
│
├── codebase-docs/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── code-to-prd/
│       └── local-wiki/
│
├── repo-instructions/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   ├── references/
│   └── skills/
│       ├── init/
│       ├── review/
│       └── copilot-review-customizer/
│           ├── SKILL.md
│           └── references/
│
├── humanizer/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   └── skills/humanizer/SKILL.md
│
├── codex-ubuntu-server/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   └── skills/codex-ubuntu-server/
│       ├── SKILL.md
│       ├── references/
│       ├── agents/openai.yaml
│       └── assets/icon.svg
│
├── artur-plugin-creator/
│   ├── plugin.json                   # portable/OpenAI manifest
│   ├── .claude-plugin/plugin.json
│   ├── references/platform-contracts.md
│   └── skills/
│       ├── create-plugin/
│       ├── inspect-plugin/
│       └── update-plugin/
│
└── uncompromising-handover/
    ├── plugin.json                   # portable/OpenAI manifest
    ├── .claude-plugin/plugin.json
    └── skills/uncompromising-handover/
        ├── SKILL.md
        ├── agents/openai.yaml
        └── assets/
```

The portable plugins other than `system-architect` use the canonical root `plugin.json` without adding duplicate `.codex-plugin/plugin.json` compatibility manifests. `system-architect` retains its existing compatibility overlay.

---

# 7. Project-specific runtime and verification boundaries

## `audit-workflow`

- Requires `python3`; the local integrations target macOS/Linux Claude Code and Codex.
- `feature-scattering` helper requires Python 3.10+.
- Native Windows is not claimed as a supported full-runtime target by this repository version.
- Cowork runtime behavior for Python hooks and the local stdio MCP server is not claimed as verified.
- Available in both repository marketplaces. Codex requires a local Python runtime, explicit MCP project roots, and trusted hooks; installed-host verification remains separate from package checks.
- `deep-review` and `feature-scattering` are read-only by default and do not replace the canonical audit lifecycle/runtime.

## `system-architect`

- Adds optional implementation-planning profiles and `/system-architect:recover` while keeping `/system-architect:architect` canonical.
- No additional local runtime dependency.

## `prompt-design`

- Skill/reference-only package; no hooks, MCP server, or helper runtime.

## `human-runbooks`

- Skill-only package; no persistent state or autonomous runtime.

## `codebase-docs`

- Python 3.10+ is required for bundled helper scripts.
- `code-to-prd` analysis and scaffolding are separate operations; a populated scaffold destination is refused rather than recursively replaced.
- `local-wiki` Markdown operations are standard-library only.
- Optional HTML rendering uses the skill-local Jinja2/markdown-it-py requirements and runs only when requested/authorized.
- Helper-backed behavior requires a host with local repository access and Python execution; plugin discovery alone does not prove those operations can run on every chat surface.

## `repo-instructions`

- `review` is read-only by default.
- Host instruction-loading behavior is version-sensitive; re-check current host behavior when it differs from this guide.
- `copilot-review-customizer` targets GitHub Copilot Code Review customization, not generic instruction maintenance. It requires live documentation and repository evidence; connection availability and requested writes are separate concerns.

## `humanizer`

- Skill-only prose editor; no runtime, hooks, MCP server, or automatic processing of other skills' output.
- Content accuracy and protected technical spans take precedence over stylistic changes.

## `codex-ubuntu-server`

- Instructions only; no bundled updater or daemon. Requires access to the selected Ubuntu host for actual operations. Changing an installation or remote-control service must be authorized, and installed-host behavior remains unverified by package checks.

## `uncompromising-handover`

- Skill and template only. A completed checkpoint must be readable by its recipient; a local file path alone is not proof of transfer.

## `artur-plugin-creator`

- Shared instruction skills, not a bundled Plugin Creator service. Source/ZIP work
  uses the host's file tools; live inspection/publication needs separately connected
  backend tools. Backend IDs, release guards, and hosted results do not apply to a
  local archive. Claimed host behavior still requires actual host execution.

## Verification boundary

The repository's structural validator, Python compilation, and maintained helper checks are the repository-level validation boundary. Keep structural/package validation separate from installed-host execution:

```text
package is present and structurally valid
!=
plugin behavior has been executed successfully in every target host
```

---

# 8. Recommended install sets

## Architecture only

Claude:

```bash
claude plugin install system-architect@artur-plugins
```

Codex:

```bash
codex plugin add system-architect@artur-plugins
```

## Review / audit

```bash
claude plugin install audit-workflow@artur-plugins
```

Start read-only review with `/audit-workflow:deep-review` in Claude Code.
In Codex, install `audit-workflow@artur-plugins` with `codex plugin add`, review
its hooks with `/hooks`, and invoke `$deep-review`.

## Portable authoring/tooling set

Claude:

```bash
claude plugin install prompt-design@artur-plugins
claude plugin install human-runbooks@artur-plugins
claude plugin install codebase-docs@artur-plugins
claude plugin install repo-instructions@artur-plugins
claude plugin install humanizer@artur-plugins
claude plugin install uncompromising-handover@artur-plugins
claude plugin install artur-plugin-creator@artur-plugins
```

Codex:

```bash
codex plugin add prompt-design@artur-plugins
codex plugin add human-runbooks@artur-plugins
codex plugin add codebase-docs@artur-plugins
codex plugin add repo-instructions@artur-plugins
codex plugin add humanizer@artur-plugins
codex plugin add uncompromising-handover@artur-plugins
codex plugin add artur-plugin-creator@artur-plugins
```

For Codex administration on Ubuntu, install `codex-ubuntu-server@artur-plugins` separately with the appropriate Claude or Codex plugin command.

There is no requirement to install the entire marketplace. Each plugin is a separate product boundary.

---

# 9. Repository validation

The repository's GitHub Actions workflow validates both marketplace registries, plugin metadata/frontmatter, local package links, manifest identity/version consistency, OpenAI interface/category consistency, required layout invariants, and maintained Python helpers.

Local validation from the repository root:

```bash
claude plugin validate --strict plugins/audit-workflow
claude plugin validate --strict plugins/system-architect
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

`claude plugin validate` validates Claude plugin manifests; `scripts/validate_plugins.py` is this repository's cross-marketplace structural validator. Passing either does not substitute for invoking the installed plugin on the target host.

---

# 10. Official references

## Anthropic

- Claude Code plugin installation and management: https://code.claude.com/docs/en/plugins/install
- Claude Code marketplace hosting and local in-place sources: https://code.claude.com/docs/en/plugins/host-marketplace
- Claude Code plugin manifest reference: https://code.claude.com/docs/en/plugins-reference
- Claude app plugins: https://claude.com/docs/plugins/overview
- Plugin feature support across Claude surfaces: https://claude.com/docs/plugins/platform-support
- Cowork plugin installation: https://claude.com/docs/cowork/guide/plugins

## OpenAI

- Plugins in ChatGPT and Codex: https://learn.chatgpt.com/docs/plugins
- Markdown: https://learn.chatgpt.com/docs/plugins.md
- Codex plugin CLI commands: https://learn.chatgpt.com/docs/developer-commands
- Markdown: https://learn.chatgpt.com/docs/developer-commands.md
- Plugin packaging and repository marketplaces: https://developers.openai.com/plugins/build/plugins
- Plugin architecture: https://developers.openai.com/plugins/concepts/plugins
