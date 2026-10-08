# claude-plugins

**Artur Plugins** is one installable engineering toolkit for Claude Code and Codex.
Architecture, audits, documentation, repository guidance, prompts, writing,
operations, handover, plugin authoring, and installation management share one package and one namespace:
`artur-plugins`. The marketplace is also named `artur-plugins`.

Skills load for the requested task; installing the toolkit does not authorize
changes, initiate an audit, run every workflow, or enable external services.
The existing audit engine, MCP server, role boundaries, references, templates,
and helper tools are retained. There are no nested standalone plugins.

## Skill catalog

Use `/artur-plugins:<skill>` in Claude Code or `$<skill>` in Codex.

| Workflow | Skills | Requirements |
|---|---|---|
| Audit and review | `deep-review`, `feature-scattering`, `audit-init`, `audit-status`, `audit-next`, `audit-discovery`, `audit-triage`, `audit-resolution`, `audit-verification` | Python for local audit/MCP/hooks and scanning; Git history optional |
| Architecture and recovery | `architect`, `recover` | Source/requirements for the requested scope |
| Prompts | `design-prompts` | Model/tool contract when target-specific |
| Human procedures | `human-execution-runbook` | Actual operational inputs and execution evidence |
| Codebase documentation | `code-to-prd`, `local-wiki` | Python; optional HTML renderer dependencies |
| Repository instructions | `init-repo-instructions`, `review-repo-instructions`, `copilot-review-customizer` | Actual repository and current host/GitHub documentation |
| Prose editing | `humanizer` | Supplied text and requested writing style |
| Codex on Ubuntu | `codex-ubuntu-server` | Access to the selected Ubuntu host |
| Session continuity | `uncompromising-handover` | An accessible checkpoint destination |
| Plugin authoring | `create-plugin`, `inspect-plugin`, `update-plugin` | Local files; connected Plugin Creator only for hosted operations |
| Plugin installation and management | [`install-agent-plugins`](skills/install-agent-plugins/SKILL.md) | Access to the selected host plugin manager/CLI; no Plugin Creator backend required |

Python 3.10+ is required for the bundled runtime and helpers. Other skills do not
require Python merely to read their instructions. No new agent framework or
mandatory session-start methodology is installed. Audit hooks only act on the
selected project's audit records; unrelated work stays outside that lifecycle.

For plugin installation and installed-copy updates, use
`/artur-plugins:install-agent-plugins` in Claude Code or `$install-agent-plugins`
in Codex. It covers other plugins as well as this toolkit. `update-plugin` edits
source/publishes a release; it is not an installer.

For the **first installation of this toolkit**, use the native commands in
[Claude Code installation](#11-install-from-github) or
[Codex installation](#31-install-from-github), or the
[local source procedure](#4-work-from-a-local-clone). A skill bundled inside an
uninstalled plugin cannot bootstrap its own discovery. The same
[installation skill source](skills/install-agent-plugins/SKILL.md) can be read
from the checkout/archive before installation.

## Package and host boundaries

Both marketplaces contain **one entry pointing to this repository root**. Claude
uses `.claude-plugin/plugin.json`. Codex uses `.codex-plugin/plugin.json`, which
explicitly selects the shared skills, its MCP config, and `hooks/codex.json`.
There is intentionally no portable root `plugin.json`: the inspected Codex
AgentPlugin loader skips hook sources for that format. The supported native
Codex format takes the hook-loading path instead. This is a compatibility choice
for this toolkit, not a universal rule against portable plugins.

After installation, inspect and trust the hooks in the target host and confirm
an actual deny/allow round trip. Package validation and direct helper execution
do not prove installed-host behavior. See [audit activation](docs/audit/README.md#codex-hook-activation).

---

# 1. Claude Code

## 1.1 Install from GitHub

Register the GitHub marketplace once. Inspect existing registrations first; reuse a matching source and do not silently replace another source with the same name.

Inside a Claude Code session:

```text
/plugin marketplace add garbageek/claude-plugins
```

Or from the shell:

```bash
claude plugin marketplace add garbageek/claude-plugins
```

Install the toolkit once:

```text
/plugin install artur-plugins@artur-plugins
```

Shell equivalent:

```bash
claude plugin install artur-plugins@artur-plugins
```

Each interactive `/plugin install ...` opens plugin details first so you can review the package and choose the installation scope.

## 1.2 Choose the Claude install scope

| Scope | Meaning | Settings file |
|---|---|---|
| `user` | Available to you in every project on this machine | `~/.claude/settings.json` |
| `project` | Enabled for collaborators in this repository | `.claude/settings.json` |
| `local` | Enabled only for you in this repository | `.claude/settings.local.json` |

Choose one scope, rather than running all three examples:

```bash
claude plugin install artur-plugins@artur-plugins --scope user
claude plugin install artur-plugins@artur-plugins --scope project
claude plugin install artur-plugins@artur-plugins --scope local
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

Inspect the installed toolkit:

```bash
claude plugin details artur-plugins
```

### Skill entry points

All entry points use the [shared skill catalog](#skill-catalog). Existing audit
actors retain their names; the Claude namespace is now `/artur-plugins:`.
The former instruction skills `init` and `review` have explicit names
`init-repo-instructions` and `review-repo-instructions` to avoid ambiguity.

### Audit and review
Read-only investigation can now start without creating audit state:

```text
/artur-plugins:deep-review
/artur-plugins:feature-scattering
```

`deep-review` checks the reported path, affected consumers, and independent failure possibilities within the requested scope. It preserves product intent, distinguishes unfamiliar mechanisms from unnecessary ones, and can route to click-path, test-quality, and operator-surface analysis when relevant. `feature-scattering` uses its bundled scanner but does not create tickets by default.

Ticket-lifecycle first run remains:

```text
/artur-plugins:audit-init
/artur-plugins:audit-status
```

Normal lifecycle flows remain:

```text
/artur-plugins:audit-discovery
/artur-plugins:audit-triage
/artur-plugins:audit-resolution
/artur-plugins:audit-verification
```

The canonical Python CLI fallback requires the actual installed plugin path
and the target project path; Claude hook substitutions are not guaranteed in a
normal Bash session:

```bash
export AUDIT_PLUGIN_ROOT="/absolute/installed/artur-plugins"
export AUDIT_PROJECT_DIR="/absolute/target/project"
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" init
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" doctor
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" summary
```

Replace these placeholders with observed absolute paths.

From the toolkit repository root, keep the target project explicit:

```bash
python3 scripts/audit.py --root "/absolute/target/project" <command> [options]
```

### Architecture and recovery
Use the canonical architecture workflow for normal architecture work:

```text
/artur-plugins:architect
```

The architect now includes optional epic, milestone, and roadmap output profiles plus focused CLI-contract guidance. Damaged-project assessment/recovery is a separate entry point:

```text
/artur-plugins:recover
```

Recovery assessment is read-only by default; recovery actions require explicit authorization.

### Prompt design
```text
/artur-plugins:design-prompts
```

Supports prompt creation, rewrite, diagnosis, adaptation, evaluation, and source-backed service-to-prompt translation.

### Human runbooks
```text
/artur-plugins:human-execution-runbook
```

Supports drafting, updating from actual execution evidence, and resuming interrupted human-executed procedures. Small procedures remain compact. Staged procedures define entry conditions, durable exits, and re-entry evidence; a final consistency check covers the affected sequence without claiming the human performed it.

### Codebase documentation
```text
/artur-plugins:code-to-prd
/artur-plugins:local-wiki
```

`code-to-prd` separates analysis/inventory from PRD scaffolding. Its helpers require Python 3.10+ and refuse destructive scaffolding into a populated destination.

`local-wiki` supports Markdown wiki finalization, validation, Markdown bundle export, and optional offline HTML output. Markdown operations use the standard library. HTML rendering additionally uses the skill-local `Jinja2` and `markdown-it-py` dependency list and should only install those dependencies when authorized.

### Repository instructions
```text
/artur-plugins:init-repo-instructions
/artur-plugins:review-repo-instructions
/artur-plugins:copilot-review-customizer
```

`init-repo-instructions` creates instructions only for the requested host/scope. `review-repo-instructions` is read-only by default and checks actual repository evidence plus current Claude/Codex instruction-loading behavior.

[copilot-review-customizer](skills/copilot-review-customizer/SKILL.md) researches a concrete repository, mines usable review/regression history, and chooses the minimum Copilot Code Review customization. It supports analysis, complete files with placement paths, or an explicitly requested PR. Its contract ledger and three local references remain part of the workflow. Live GitHub documentation must confirm any mechanism it relies on; the mechanics reference is a starting point, not a reason to skip verification.

Installing the toolkit supplies the **customizer**, not a review skill already installed in another repository. The customizer may produce `.github/skills/code-review/SKILL.md` in the selected project, update another appropriate surface, or conclude no change is needed. It needs documentation access and repository/history evidence; it prefers a GitHub connector and requests archives, a checkout, or command output when that access is unavailable. No GitHub connection, credentials, settings changes, or automatic reviews are provisioned by this package. Preparing files and confirming documented loading do not prove Copilot used them or improved a real review.

### Prose editing
```text
/artur-plugins:humanizer
```

[humanizer](skills/humanizer/SKILL.md) detects, rewrites, or edits formulaic prose when writing quality is requested. It handles technical documentation, PR descriptions, review comments, messages, and other prose while preserving meaning, certainty, code, identifiers, numbers, citations, and the sender's authority and commitments. Detect mode does not rewrite; already-clear text may remain unchanged. This is prose editing, not prompt design, an authorship detector, or an automatic filter on unrelated answers.

### Codex on Ubuntu

Use `/artur-plugins:codex-ubuntu-server` to administer Codex CLI on a selected Ubuntu host. The skill requires access to that host and does not authorize installation, updates, remote control, or service changes without the relevant request. It contains setup and maintenance references.

### Session handover

Use `/artur-plugins:uncompromising-handover` to create a self-contained continuation checkpoint for an active coding task. The bundled template is the source of the output format; checkpoint files are versioned and must not be committed automatically.

### Plugin authoring

The [plugin authoring skills](skills/create-plugin/SKILL.md)
create, inspect, and update plugins for Claude Code, Codex, or both. It selects
portable or native manifests for the required client capabilities and shares
skills. MCP, hooks, and agents need actual host adapters, not a compatibility label.
Local repository/archive work does not require the Plugin Creator backend.

Use `create-plugin` for a new package, `inspect-plugin` for read-only inspection,
and `update-plugin` for changes or conversion. Hosted publication is optional and
requires the separately connected backend. Updates use release guards and explicit
`delete_paths`; omitting a file from an upload is not deletion. Preparing an archive
does not publish to a Claude account, an OpenAI account, GitHub, or a public directory.

### Plugin installation and management

Use `/artur-plugins:install-agent-plugins` in Claude Code or
`$install-agent-plugins` in Codex to install, enable, disable, upgrade, remove, or
troubleshoot a client installation. The skill reads the actual target host and
marketplace identity, distinguishes source registration from installation, and
checks the installed copy separately from MCP/hook activation. It also covers
Claude account uploads, local development loading, private sources, cache drift,
and migration from the former standalone installations.

[Full workflow](skills/install-agent-plugins/SKILL.md). No hosted Plugin Creator
backend is needed. It does not modify plugin source or publish a release to
satisfy an installed-version update, and it never treats commands for another
machine as executed actions.

## 1.4 Enable or disable

Enable or disable the toolkit:

```bash
claude plugin disable artur-plugins@artur-plugins
claude plugin enable artur-plugins@artur-plugins
```

You can also use `/plugin` -> **Installed** and press **Space** on a plugin.

## 1.5 Update

Refresh only the marketplace listing:

```bash
claude plugin marketplace update artur-plugins
```

Update the installed toolkit:

```bash
claude plugin update artur-plugins@artur-plugins
```

This one plugin update updates all bundled workflows.

These operations are different:

```text
marketplace update -> refreshes marketplace metadata/listing
plugin update      -> updates one installed plugin
```

To refresh the marketplace and update all plugins installed from it in one operation, open `/plugin` -> **Marketplaces** -> `artur-plugins` -> **Update marketplace**.

Third-party marketplaces have auto-update disabled by default. Enable it from `/plugin` -> **Marketplaces** -> `artur-plugins` -> **Enable auto-update** if desired.

The current session keeps the plugin version already loaded until you run `/reload-plugins` or start a new session.

## 1.6 Replace earlier standalone installations

This package has a new shared identity; a marketplace refresh does not uninstall
previously installed standalone products. Inspect `/plugin` -> **Installed** (or
`claude plugin list`), then disable/remove the previous standalone entries from
this repository at their actual installation scopes. Do not remove the marketplace.
Keeping the old audit plugin active alongside this one can register duplicate MCP
servers and hooks. Check for account-synced copies and manually configured hooks too.

Install `artur-plugins@artur-plugins`, then `/reload-plugins` or start a new session.
Use `/artur-plugins:<skill>`; `init`/`review` are now `init-repo-instructions` and
`review-repo-instructions`. The old init/status/next commands are shared skills,
not duplicate command files. Keep the project's `audit/` state and existing
handover files; consolidation does not require a data migration.

Remove only obsolete manual hook entries after confirming the new hooks work.
Never overwrite an entire user/project hook file or delete unrelated handlers.

## 1.7 Remove

Remove the toolkit:

```bash
claude plugin uninstall artur-plugins@artur-plugins
```

Remove the marketplace separately when no longer needed:

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

Cloud sessions have a separate execution environment and capability set. Check the selected surface’s current supported setup path; do not assume a local plugin installation is available there.

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

The `artur-plugins` marketplace exposes the single `artur-plugins` toolkit described in the [skill catalog](#skill-catalog).

Use the repository marketplace, or upload this one-plugin archive through the Claude app's supported plugin-upload flow. The archive contains exactly one Claude manifest.

## 2.1 Account sync to Claude Code

A plugin installed on your Claude account can sync down to Claude Code when Claude Code starts while signed in to the same account. It appears with an ID such as:

```text
<plugin>@synced
```

The reverse does not happen automatically: a plugin installed only with `/plugin` or `claude plugin install` remains on that machine and is not added to your Claude account.

## 2.2 Surface differences

### Instruction-only workflows

Architecture, prompt design, human runbooks, repository instructions, prose editing, handover, plugin authoring, and installation management are skill/reference workflows. They do not require executing a bundled local runtime to read or follow the instructions. Actual file, web, and connected-service capabilities still depend on the host; packaging is not proof of execution parity.

### Codebase documentation

The skills can load as plugin content, but its practical repository-analysis workflows use local Python helpers and local source files. Full helper-backed behavior therefore depends on a host that can access the repository and run Python 3.10+. Optional HTML wiki rendering has additional skill-local Python dependencies.

### Audit and review

The audit subsystem contains shared skills, Claude role agents, hooks, a local stdio MCP server, and a Python runtime:

- **Claude Code:** full intended target; skills, role agents, hooks, MCP tools, and Python runtime are packaged together.
- **Claude Chat:** skill content can load, while agents, hooks, and the local MCP runtime do not provide the same lifecycle runtime.
- **Cowork:** agents, hooks, and a local MCP server can load when the session runs on your computer, but this repository does not claim the `audit-workflow` Cowork runtime as verified; `python3` is required there.

The plugin deliberately has no top-level `bin/` directory because Claude Chat/Cowork installation rejects plugins that contain one.

---

# 3. OpenAI Codex

The native repository marketplace is:

```text
.agents/plugins/marketplace.json
```

It exposes the same single toolkit and shared skills. Codex selects its native
manifest, shared MCP runtime, and hook definitions. Protected audit lifecycle
behavior still requires registered, trusted hooks verified in the installed host.

## 3.1 Install from GitHub

Register the GitHub marketplace:

```bash
codex plugin marketplace add garbageek/claude-plugins
```

Verify the source:

```bash
codex plugin marketplace list
```

Install the toolkit:

```bash
codex plugin add artur-plugins@artur-plugins
```

Equivalent explicit marketplace form:

```bash
codex plugin add artur-plugins --marketplace artur-plugins
```

or:

```bash
codex plugin add artur-plugins -m artur-plugins
```

Verify installed and available plugins:

```bash
codex plugin list
codex plugin list --json
codex plugin list --marketplace artur-plugins --available --json
```

`--available` includes marketplace plugins that are not installed and requires
`--json`; being listed as available does not prove installation. `codex plugin add
artur-plugins@artur-plugins --json` returns the installed identity/version and
`installedPath`. Inspect that actual runtime copy rather than assuming the source
checkout was updated in place.

Do not use `codex plugin install`; the documented Codex subcommand is `codex plugin add`.

## 3.2 Interactive installation and enablement

Start Codex and open:

```text
/plugins
```

Switch to the `artur-plugins` marketplace, open `artur-plugins`, and install it. Press **Space** on an installed plugin to enable or disable it.

In the ChatGPT desktop app, open the **Plugins** tab, select `artur-plugins`, and install `artur-plugins`.

Start a new chat or CLI session before first use so bundled skills and plugin content are loaded.

### Audit Workflow in Codex

The native Codex manifest explicitly selects `hooks/codex.json` and
`mcp/codex.json`. Inspect `/hooks`, review/trust the definitions, and verify a
real blocked status edit plus an allowed evidence edit before relying on audit
guardrails. See [audit activation](docs/audit/README.md#codex-hook-activation).

Use `$audit-init`, `$audit-status`, `$audit-next`, and the role/review skills in
the catalog. Status/queue inspection does not initialize state. Pass an absolute
project `root` to every `audit_*` MCP call. Both host configurations require it
and reject the installed package directory as an audit workspace.

Verification uses a fresh native subagent or a separate independent session.
Changing the resolver's role name does not establish independence. See the
[audit invocation contract](docs/audit/CONTRACT.md#1-canonical-runtime-invocation)
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

### Replace earlier installations or refresh stale content

Use `/plugins` or `codex plugin list` to identify earlier standalone packages from
this repository. Disable/remove them separately before relying on this toolkit's
MCP and hooks. Also remove only obsolete manual audit-hook registrations after
confirming the new plugin handlers work. Preserve unrelated configuration and
project `audit/` data.

Refresh the marketplace and install the unified package:

```bash
codex plugin marketplace upgrade artur-plugins
codex plugin add artur-plugins@artur-plugins
```

If an existing unified installation still serves stale cached content, inspect the
installed source/version and reinstall through `/plugins` or remove/add the same
package. Restart the session and review any changed hook trust definitions. A
marketplace refresh and installed-package refresh are not the same evidence.

## 3.4 Remove

Remove the installed toolkit:

```bash
codex plugin remove artur-plugins@artur-plugins
```

Equivalent explicit marketplace form:

```bash
codex plugin remove artur-plugins --marketplace artur-plugins
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
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
└── skills/
```

## 4.1 Claude Code local marketplace

Inside Claude Code from the repository root:

```text
/plugin marketplace add .
/plugin install artur-plugins@artur-plugins
/reload-plugins
```

The Claude marketplace references the repository root with `source: "./"`. When registered from this local directory, Claude Code loads the toolkit in place. Source edits become visible on the next session start or after `/reload-plugins`, without a version bump.

For one-session development of one plugin without installing the marketplace:

```bash
claude --plugin-dir .
```

This loads the one toolkit directly; no per-workflow installation is needed.

## 4.2 Codex local marketplace

From the repository root:

```bash
codex plugin marketplace add .
codex plugin list --marketplace artur-plugins --available --json
```

Install the unified toolkit:

```bash
codex plugin add artur-plugins@artur-plugins
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

If source changes are not reflected, inspect the actual installed path/version
and use the supported reinstall/reload flow. `codex plugin marketplace upgrade`
refreshes Git marketplaces, not this local directory source. Preserve the selected
source, enablement and relevant setup across a reinstall. Do not edit host cache
files by hand or use sparse checkout for this root plugin that omits its shared
skills, hooks, MCP, references or scripts.

## 4.3 Repo-local Codex enablement

In a trusted project's `.codex/config.toml`:

```toml
[plugins."artur-plugins@artur-plugins"]
enabled = true
```

Set `enabled = false` to disable the toolkit for that project without uninstalling
it. This is plugin enablement, not hook trust. Codex reads project configuration
only for trusted projects. Do not add these settings to other projects implicitly.

---

# 5. One plugin, two host manifests

Both marketplace files keep the name `artur-plugins` and contain one entry whose
source is `./`. Claude uses its own catalog format; Codex uses its native catalog
format. Neither points at a nested product or duplicates the skills/runtime.

`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` carry synchronized
identity, version, and description. Codex's manifest selects `./skills/`,
`./hooks/codex.json`, and `./mcp/codex.json`. Claude uses the default `skills/`,
`agents/`, `hooks/hooks.json`, and `.mcp.json` locations.

The native Codex manifest is deliberate, not a redundant overlay: without a root
portable `plugin.json`, Codex selects its legacy/native hook-capable loading path.
Adding a portable root would change that selected format and may disable hooks in
the inspected loader. New unrelated plugins may still use portable manifests;
choose their format from the target client's actual capabilities.

Sources: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins),
[Codex loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs),
[Claude manifest reference](https://code.claude.com/docs/en/plugins-reference).

---

# 6. Repository layout relevant to installation

```text
claude-plugins/
├── .claude-plugin/
│   ├── plugin.json          # Claude identity
│   └── marketplace.json     # one entry -> ./
├── .codex-plugin/
│   └── plugin.json          # Codex identity and component selection
├── .agents/plugins/
│   └── marketplace.json     # one entry -> ./
├── .mcp.json                # Claude -> shared audit server
├── mcp/
│   ├── codex.json           # Codex -> same audit server
│   └── audit_mcp_server.py
├── hooks/                   # two declarations, one guard
├── scripts/                 # audit runtime, scanner, validator
├── skills/                  # shared independent skill entry points
├── agents/                  # Claude audit role agents
├── references/              # shared authoring/instruction contracts
├── docs/audit/              # canonical lifecycle contract and operator guide
└── .github/workflows/       # package validation
```

Skill-specific references, templates, scripts and icons remain within their skills.
There is no old `plugins/<product>/` tree, duplicate command wrapper tree, or second
audit runtime. Resources resolve from the installed package, not the development
checkout; generated project state belongs to the selected external workspace.

---

# 7. Project-specific runtime and verification boundaries

## Audit lifecycle

- Requires `python3`; the local integrations target macOS/Linux Claude Code and Codex.
- `feature-scattering` helper requires Python 3.10+.
- Native Windows is not claimed as a supported full-runtime target by this repository version.
- Cowork runtime behavior for Python hooks and the local stdio MCP server is not claimed as verified.
- Included in the unified toolkit for both hosts. Codex uses a native hook-capable manifest; local Python, explicit project roots, hook trust, and installed-host verification are still required. See [activation](docs/audit/README.md#codex-hook-activation).
- `deep-review` and `feature-scattering` are read-only by default and do not replace the canonical audit lifecycle/runtime.

## Architecture and recovery

- Adds optional implementation-planning profiles and `/artur-plugins:recover` while keeping `/artur-plugins:architect` canonical.
- No additional local runtime dependency.

## Prompt design

- Instruction-only workflow; no separate hooks, MCP server, or helper runtime.

## Human runbooks

- Instruction-only workflow; no autonomous runtime. Execution state lives in the requested runbook.

## Codebase documentation

- Python 3.10+ is required for bundled helper scripts.
- `code-to-prd` analysis and scaffolding are separate operations; a populated scaffold destination is refused rather than recursively replaced.
- `local-wiki` Markdown operations are standard-library only.
- Optional HTML rendering uses the skill-local Jinja2/markdown-it-py requirements and runs only when requested/authorized.
- Helper-backed behavior requires a host with local repository access and Python execution; plugin discovery alone does not prove those operations can run on every chat surface.

## Repository instructions

- `review-repo-instructions` is read-only by default.
- Host instruction-loading behavior is version-sensitive; re-check current host behavior when it differs from this guide.
- `copilot-review-customizer` targets GitHub Copilot Code Review customization, not generic instruction maintenance. It requires live documentation and repository evidence; connection availability and requested writes are separate concerns.

## Prose editing

- Prose-editing workflow; no additional runtime or automatic processing of other skills' output.
- Content accuracy and protected technical spans take precedence over stylistic changes.

## Codex on Ubuntu

- Instructions only; no bundled updater or daemon. Requires access to the selected Ubuntu host for actual operations. Changing an installation or remote-control service must be authorized, and installed-host behavior remains unverified by package checks.

## Session handover

- Skill and template only. A completed checkpoint must be readable by its recipient; a local file path alone is not proof of transfer.

## Plugin authoring

- Shared instruction skills, not a bundled Plugin Creator service. Source/ZIP work
  uses the host's file tools; live inspection/publication needs separately connected
  backend tools. Backend IDs, release guards, and hosted results do not apply to a
  local archive. Claimed host behavior still requires actual host execution.

## Plugin installation and management

- Uses the selected host's existing plugin manager, CLI or supported UI, not a new installer service.
- Distinguishes registration, installation, enablement, skill discovery, MCP connection and hook execution.
- Instructions printed for another machine do not establish installation on that machine.
- Preserves local versus account scope and existing settings; publishing new source is a separate workflow.

## Verification boundary

The repository's structural validator, Python compilation, and maintained helper checks are the repository-level validation boundary. Keep structural/package validation separate from installed-host execution:

```text
package is present and structurally valid
!=
plugin behavior has been executed successfully in every target host
```

---

# 8. Choose the workflow, not another installation

Install `artur-plugins` once, then invoke only the relevant skill. Examples:

```text
/artur-plugins:architect
/artur-plugins:deep-review
/artur-plugins:code-to-prd
/artur-plugins:create-plugin
/artur-plugins:install-agent-plugins
```

Codex uses the same names with `$`, for example `$architect`, `$deep-review`, or
`$install-agent-plugins`.
Read-only review does not start a ticket lifecycle. A prompt request produces a
prompt, not an unrequested implementation. Handover creates the requested checkpoint,
not a new workflow engine. Plugin publication and Ubuntu maintenance require their
own explicit action request and available tools; installation does not authorize
external writes.

---

# 9. Repository validation

The repository's GitHub Actions workflow validates both marketplace registries,
plugin metadata/frontmatter, local package links, manifest identity/version
consistency, OpenAI interface/category consistency, required layout invariants,
and maintained Python helpers. It also rejects skill directories without an entry
file and an incomplete create/inspect/update/install plugin workflow set; valid
remaining files must not hide a missing required skill.

Local validation from the repository root:

```bash
python3 -m pip install PyYAML==6.0.3
python3 scripts/validate_plugins.py
python3 -m compileall -q scripts hooks mcp skills
# When Claude Code is installed:
claude plugin validate --strict .
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
