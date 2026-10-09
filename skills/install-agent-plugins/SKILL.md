---
name: "install-agent-plugins"
description: "Use when installing, enabling, disabling, upgrading, removing, or troubleshooting installed plugins and marketplaces in Claude Code, the Claude app, or Codex. Also use for local plugin development loading and translating installation commands between hosts; not for editing plugin source or publishing a release."
---

# Plugins in Claude Code, Claude app, and OpenAI Codex

Claude and Codex both use plugins and marketplaces, but their mechanisms differ.
Never assume a Claude command works in Codex or vice versa. Check the selected
host's current official documentation and installed CLI help for version-sensitive
behavior; distinguish documented capability from behavior actually observed.

## Route the requested operation

This skill manages **installation state on a selected host**, not plugin source
versions or backend releases. For creating a package use
[create-plugin](../create-plugin/SKILL.md); for source/archive changes or publishing
a new backend release use [update-plugin](../update-plugin/SKILL.md). For package
content or compatibility review use [inspect-plugin](../inspect-plugin/SKILL.md).
Installing/upgrading the Codex CLI itself on Ubuntu belongs to
[codex-ubuntu-server](../codex-ubuntu-server/SKILL.md).

## Resolve the target before changing it

1. Identify the requested action, client/surface, actual machine and user, plugin,
   source, marketplace name, and installation scope. Reuse supplied facts; ask only
   for an unresolved detail that changes the destination or intended action.
2. Discover the available execution/UI tools. A shell in this agent's container
   is not the user's desktop or remote server. Run commands only on the requested
   target; otherwise return its exact procedure and state that it was not run.
   Do not install or upgrade the host CLI just to answer a plugin request.
3. Inspect existing marketplace and installed-plugin state with that host's list
   commands/UI. Derive plugin and marketplace identities from the selected
   manifests or listing, not from the repository name or ZIP filename. Confirm
   an existing marketplace with the same name points to the intended source.
   Do not replace an unrelated source or disable unrelated plugins silently.
4. Use the requested scope. For a new shell install with no specified scope, keep
   the host's documented default and report it. For updates/removals preserve the
   existing scope, source, enabled state and settings; do not accidentally add a
   user-scoped copy when the project-scoped install was requested.
5. Perform only the requested operation. An installation question or inspection
   is read-only. Plugin installation does not authorize publishing, Git pushes,
   broad config rewrites, automatic hook trust, or connecting unrelated accounts.
   Preserve existing config entries. A marketplace removal has wider effects than
   a single-plugin removal: inspect and disclose its affected installations first.

Use the host's supported installer/UI rather than manually editing its cache.
Read [package contracts](../../references/plugin-authoring.md) when layout,
manifest precedence, runtime dependencies or component loading affect installation.
Do not convert a working native package to portable format as an install step.

## Core rule

Registering a marketplace is NOT installing a plugin. For marketplace-based
third-party installs, ensure the intended source is registered, then install the
selected plugin. Reuse a matching registration rather than adding it again.
Account uploads and one-session development loading use their separate flows:

| Step | Claude Code | Codex |
| --- | --- | --- |
| 1. Register source | `claude plugin marketplace add owner/repo` | `codex plugin marketplace add owner/repo` |
| 2. Install plugin | `claude plugin install <plugin>@<marketplace>` | `codex plugin add <plugin>@<marketplace>` |

`<marketplace>` is the `name` field in the marketplace's `marketplace.json`, not the repository name.

## Quick reference

| Task | Claude Code | Codex |
| --- | --- | --- |
| Browse | `/plugin`; `/plugin directory` where supported | `/plugins` (CLI) or the desktop Plugins tab |
| Install | `/plugin install <p>@<m>` or `claude plugin install ...` | `codex plugin add <p>@<m>` or `/plugins` |
| Add Git marketplace | `claude plugin marketplace add owner/repo` | `codex plugin marketplace add owner/repo` |
| Add local marketplace | `claude plugin marketplace add ./path` | `codex plugin marketplace add ./path` |
| List marketplaces | `claude plugin marketplace list` | `codex plugin marketplace list` |
| Refresh marketplace | `claude plugin marketplace update <name>` | `codex plugin marketplace upgrade [<name>]` |
| Remove marketplace | `claude plugin marketplace remove <name>` | `codex plugin marketplace remove <name>` |
| List installed | `claude plugin list` | `codex plugin list` or `/plugins` |
| Update plugin | `claude plugin update <p>@<m>` | `codex plugin marketplace upgrade`, then reinstall if needed |
| Disable | `claude plugin disable <p>@<m>` | `/plugins`, Space on the installed plugin |
| Remove plugin | `claude plugin uninstall <p>@<m>` | `codex plugin remove <p>@<m>` |
| Local dev | `claude --plugin-dir ./plugin` | Local/repo marketplace + `/plugins` |

`codex plugin install` is NOT a documented subcommand. Use `add` and `remove`. Claude uses `install` and `uninstall`.

---

## Claude Code

### Official marketplace

```bash
claude                                   # official marketplace auto-registers on first interactive run
```
```text
/plugin
/plugin install <plugin>@claude-plugins-official
```

In-session `/plugin install ...` opens plugin details first so the user can review components and choose scope. Shell equivalent: `claude plugin install <plugin>@claude-plugins-official`.

Fresh machine / non-interactive setup:

```bash
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install <plugin>@claude-plugins-official
```

### Third-party marketplace

```bash
claude plugin marketplace add owner/repo
claude plugin install <plugin>@<marketplace>
```

Interactive equivalents: `/plugin marketplace add owner/repo` and `/plugin install <plugin>@<marketplace>`.

Supported sources: GitHub shorthand, full Git URLs, local paths, hosted `marketplace.json` URLs. Pin a branch or tag with `#ref`:

```bash
claude plugin marketplace add owner/repo#release-tag
claude plugin marketplace add https://gitlab.example.com/group/plugins.git#release-tag
claude plugin marketplace add ./my-marketplace
claude plugin marketplace add https://example.com/marketplace.json
```

Use an absolute local path or a relative path starting with `./` or `../`; a bare `name/name` is read as a GitHub repo. Replace example refs with an existing requested branch/tag rather than inventing one.

Where the selected Claude version supports one-step add and install:

```text
/plugin install deploy-helper --marketplace your-org/plugins
```

### Scopes

| Scope | Meaning | Settings file |
| --- | --- | --- |
| `user` (default) | You, every project on this machine | `~/.claude/settings.json` |
| `project` | Collaborators in this repo | `.claude/settings.json` |
| `local` | Only you, this repo | `.claude/settings.local.json` |

```bash
claude plugin install <plugin>@<marketplace> --scope project
```

Precedence: `local > project > user`. A committed project setting enables the plugin for collaborators but does not download it; each collaborator still runs the install with `--scope project` once.

### Apply and verify

Shell installs are available on next start. In an open session run `/reload-plugins`
(add `--force` only after reviewing a prompt-cache invalidation warning). Verify
with `claude plugin list`; inspect with `claude plugin details <plugin>` when the
installed CLI supports it. Plugin skills appear as `/<plugin>:<skill>`.
Do not send interactive slash commands to Bash as executable commands.

### Enable, disable, update, remove

```bash
claude plugin disable <plugin>@<marketplace>
claude plugin enable <plugin>@<marketplace>
claude plugin update <plugin>@<marketplace>     # updates the installed plugin
claude plugin marketplace update <marketplace>  # refreshes listing metadata only
claude plugin uninstall <plugin>@<marketplace>
claude plugin prune                             # remove unused auto-installed dependencies
claude plugin marketplace remove <marketplace>  # also uninstalls all plugins from it
```

To refresh a marketplace and update all its plugins at once: `/plugin` -> Marketplaces -> select -> Update marketplace. Third-party and local marketplaces have auto-update off by default; enable it from the same menu.

### Local development

Do not hand-copy plugins into undocumented directories. Use:

```bash
claude --plugin-dir ./path/to/plugin          # one session
claude plugin marketplace add ./my-marketplace # reusable; dir contains .claude-plugin/marketplace.json
```

Claude plugins referenced by relative-path source from a local directory
marketplace load in place; edits apply on next session start or `/reload-plugins`
without requiring a version bump for that reload. This is not permission to ship
changed released content under an unchanged version.

For a supplied ZIP, inspect and extract into an explicit retained source directory,
not an undocumented host cache. Determine whether it contains a marketplace or
one plugin. Register the extracted marketplace root when present; a standalone
Claude plugin can be loaded for one session with `--plugin-dir`. Do not pass a ZIP
path to a marketplace command that expects a repository/directory.

### Private marketplaces

Claude Code uses existing Git credentials and suppresses interactive prompts.

- HTTPS: `gh auth login` then `gh auth setup-git`.
- SSH: `claude plugin marketplace add git@github.com:your-org/private-plugins.git`. Host must be in `known_hosts`; key must work without a passphrase prompt (e.g. loaded in `ssh-agent`).
- With `owner/repo` shorthand, SSH is tried first, then HTTPS. Set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` to skip the SSH probe.
- Background auto-update uses the same credentials; if missing, it fails quietly and the last synced copy keeps working.

### Desktop app, VS Code, cloud

- Desktop app (local or SSH Code session): `+ -> Plugins -> Add plugin`; manage via `+ -> Plugins -> Manage plugins`.
- VS Code: type `/plugins`; use the Plugins and Marketplaces tabs; changes apply without restarting.
- Cloud/remote sessions are separate execution environments, not the local
  installation. Check that surface's current supported installation/configuration
  path; do not assume a local install or a repository settings file is sufficient.
  Report unavailable plugin/runtime components rather than asserting local parity.

---

## Claude app, claude.ai, Cowork

Account-level plugins are separate from Claude Code's machine-local installs. Open `Customize -> Plugins`:

- **Discover**: install from Anthropic marketplaces, the directory, and org-provided sources.
- **Add -> Add marketplace**: `owner/repo` or repo URL. GitHub, GitHub Enterprise, public GitLab and Bitbucket work. For a private GitHub repo, connect GitHub in the dialog and grant the Claude GitHub App access.
- **Add -> Upload plugin**: `.zip` or `.plugin` containing exactly one
  `.claude-plugin/plugin.json`. A repository whose root is itself **one plugin**
  can be packaged this way; a collection of independently packaged plugins cannot.
  Preserve every referenced file. Check the current upload size/format limits in
  the target UI before submission.

Updates: for added marketplaces use Check for updates, or Sync automatically (github.com marketplaces). Uploaded plugins do not update from a source.

Where the selected Claude version supports account sync, account plugins can
appear in Claude Code as `<plugin>@synced` on next start with the same account.
The reverse is not automatic: a local `claude plugin install` is not an account
publication. Inspect the actual source/scope before replacing or removing an
installation; do not confuse a synced copy with a local marketplace copy.

Component support by surface:

| Component | Chat | Cowork | Claude Code |
| --- | --- | --- | --- |
| Skills | loads | loads | loads |
| Commands | loads as a skill | loads, as `/plugin-name:command` | loads |
| Agents | ignored | loads | loads |
| Hooks | ignored | loads | loads |
| Remote MCP (`http`/`sse`, fixed URL) | works once connected on Connectors tab | loads, connect on Connectors tab | loads |
| Local MCP (command the app starts) | ignored | loads if Cowork session runs on your computer | loads |
| Top-level `bin/` executables | plugin can't be installed | plugin can't be installed | loads |

---

## OpenAI Codex

Use the selected Codex CLI/desktop plugin manager. ChatGPT account discovery,
workspace publishing, and local installation are different operations even when
they expose overlapping catalogs. Do not use local CLI commands as if they manage
the web account. Check support in the actual IDE/cloud surface rather than
assuming CLI/desktop installation propagates there.

### Install

```bash
codex
```
```text
/plugins
```

Switch marketplace tabs, open the plugin to inspect it, install, complete auth/setup prompts, then start a new chat or CLI session before first use. Press Space on an installed plugin to toggle it. In the ChatGPT desktop app use the Plugins tab, then start a new chat.

Non-interactive:

```bash
codex plugin add <plugin>@<marketplace>
codex plugin list
codex plugin remove <plugin>@<marketplace>
```

- `add`/`remove` accept `--marketplace NAME` / `-m NAME` when `@marketplace` is omitted; `list` accepts it as a filter.
- All three support `--json`. `codex plugin list --available --json` also shows
  uninstalled marketplace plugins (`--available` requires `--json`). Successful
  `add --json` returns the selected identity/version and `installedPath`; inspect
  that actual path when checking the runtime copy. Do not infer it from a filename.
- `remove` deletes the plugin from local config and cache.

### Custom marketplaces

```bash
codex plugin marketplace add owner/repo
codex plugin marketplace add owner/repo --ref main      # or owner/repo@main
codex plugin marketplace add https://github.com/example/plugins.git --sparse .agents/plugins --sparse plugins/my-plugin
codex plugin marketplace add ./local-marketplace-root
codex plugin marketplace list
codex plugin marketplace upgrade [<marketplace>]
codex plugin marketplace remove <marketplace>
```

Repeat `--sparse PATH` only when the resulting checkout still contains the chosen
plugin **and all its shared support files**. Fetching `.agents/plugins` alone can
leave catalog entries pointing to absent source. For this root-level `artur-plugins`
package, omit `--sparse` and keep the full checkout. `--json` works on marketplace
`add`, `list`, `upgrade`, and `remove`. `upgrade` refreshes **Git** marketplaces,
not local directory sources, and does not itself establish a new installed copy.
Install separately and verify the selected version/path. Restart the local desktop
client after marketplace changes when needed; do not claim a restart happened
merely because instructions were printed.

### Repo and personal marketplaces

- Repo: `$REPO_ROOT/.agents/plugins/marketplace.json` (native location)
- Personal: `~/.agents/plugins/marketplace.json`
- Common plugin locations (conventions only): `plugins/my-plugin/` in a repo, `~/.codex/plugins/<plugin>/` personally.
- The marketplace entry's `source.path` decides the real location: relative to marketplace root, starts with `./`, stays inside the root.
- Some clients also discover `.claude-plugin/marketplace.json` as a compatibility
  source. Do not guess precedence across hosts when both catalogs exist. Inspect
  the marketplace listing and installed identity/source selected by the actual
  client. In this toolkit both catalogs intentionally expose the same root plugin.

### Repo-local enable/disable

In `.codex/config.toml` (loaded only for trusted projects):

```toml
[plugins."my-plugin@local-repo"]
enabled = true   # false to disable without uninstalling
```

Key format: `<plugin-name>@<marketplace-name>`.

### Cache

The usual cache shape is `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`;
local sources can use `local` as the version directory. Treat this as a diagnostic
hint, not a path to construct and overwrite. **Source directory != installed
runtime copy.** Use the actual returned/listed installation path, source and
version to check staleness.

For a Git source, refresh its marketplace before an installed update. For a local
source, modify only the requested source and use the supported reload/reinstall
flow; a Git marketplace upgrade cannot refresh a directory source. If removal and
re-addition are necessary, record the selected source, scope, enablement and setup
first, reinstall only that plugin, and verify state afterwards. Do not invent a
`codex plugin update` command or use the authoring `update-plugin` skill to bump
source metadata merely to refresh an installed copy.

### Package layout

```text
my-plugin/
├── plugin.json        # portable manifest at plugin root
├── skills/
├── mcp.json
├── hooks/hooks.json
└── assets/
```

This tree describes the **portable Agent Plugins** format, not every valid
Codex package. OpenAI-specific settings belong under `extensions.com.openai`.
The native `.codex-plugin/plugin.json` format also works without a portable root
and can explicitly select a native MCP config and hook adapter. Do not add or
remove manifests during installation to make a package match a preferred tree.
Adding a portable root changes loader selection; an overlay does not force native
hook loading. See the shared [package contracts](../../references/plugin-authoring.md)
and the target version's actual behavior. Marketplace entries point at the plugin
**root**, never at `.codex-plugin/` or the catalog directory.

### Private repos

The source must be readable by the local environment. Register with `codex plugin marketplace add ...`, verify with `codex plugin marketplace list`, install with `codex plugin add`, `/plugins`, or the Plugins tab.

---

## Common mistakes to catch

1. Treating marketplace registration as installation (see Core rule).
2. Using `codex plugin install` or `codex plugin uninstall`; correct commands are `add` / `remove`.
3. Treating a raw Git repo as a marketplace. It needs `.claude-plugin/marketplace.json` (Claude) or `.agents/plugins/marketplace.json` (OpenAI native).
4. Pointing an OpenAI marketplace at `.codex-plugin/` instead of the plugin root.
5. Uploading a multi-plugin marketplace ZIP as one plugin. Upload one plugin per archive or use Add marketplace; a single-plugin root repository is a valid one-plugin package.
6. Assuming a committed Claude `project` setting downloads the plugin for teammates; each person must install once.
7. Assuming a local installation propagates into another desktop, IDE, cloud session or account without checking that surface.
8. Confusing `marketplace update` (metadata only) with `plugin update` (installed plugin) in Claude Code.

## Verify installation, activation, and required components

Keep these states separate: **source registered**, **plugin installed**, **enabled**,
**skills discovered**, **MCP connected**, **hooks registered/trusted/executed**.
An available catalog entry is not an installed plugin. A passing package validator
is not an installation or a runtime result. Confirm only states actually observed.

- Check the selected identity, source, version, scope and returned install path.
  Reload/restart only the appropriate host session when needed, then inspect skills
  (`/skills` where supported). Invoke a harmless/read-only entry point rather than
  a creation/publication skill just to prove discovery.
- For bundled MCP, verify its effective config and actual startup/connection in the
  host, dependency availability, and the intended target project. Do not supply the
  installed plugin directory as writable project state. A missing optional MCP
  component need not make unrelated instruction-only skills unusable.
- Inspect `/hooks` in Codex and the selected Claude hook UI/diagnostics. Installing
  or enabling a plugin is not hook trust. Portable Codex AgentPlugin loaders have
  been observed to skip hook sources; check the actual target version. Never trust
  or install duplicate global hooks silently. If registration is missing, diagnose
  the chosen loader before proposing an explicit, user-authorized fallback.
- This toolkit has no bundled hooks. Its audit lifecycle validates MCP/CLI
  operations, not direct Markdown edits. Confirm MCP availability in the installed
  host before claiming operational support.
- When moving from the old split marketplace to this unified toolkit, retain the
  shared marketplace and project audit data. Inspect installed names first; remove
  or disable only the superseded copies the user authorizes to avoid duplicate
  skills/hooks. Never remove the entire marketplace as a migration shortcut.

For self-update/removal, do not destroy the running skill/helper copy or restart
its host mid-operation. Finish output outside the install cache first and hand off
a disruptive final step to a separate session or the user. This is not a reason to
invent a background daemon or silently uninstall other packages.

## Output

Report the actual host/machine, requested action, selected plugin/source/scope,
observed install/enable/version state, reload needs and unverified components.
Commands supplied for another machine are **instructions**, not completed actions.
Do not generate an installation report file unless requested.

## Operator checklists

Claude Code: add marketplace if third-party -> install plugin -> choose scope -> `/reload-plugins` if needed -> verify with `claude plugin list` -> configure bundled connectors/MCP -> enable marketplace auto-update if wanted.

Codex: add marketplace source (custom plugins) -> verify with `codex plugin marketplace list` -> install via `codex plugin add`, `/plugins`, or Plugins tab -> verify with `codex plugin list` -> start a new chat/session -> for repo-local plugins check `.codex/config.toml` (trusted projects only).

## Official sources

Anthropic:
- https://code.claude.com/docs/en/plugins/install
- https://code.claude.com/docs/en/discover-plugins
- https://code.claude.com/docs/en/plugins/host-marketplace
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugins/create
- https://claude.com/docs/plugins/overview
- https://claude.com/docs/plugins/platform-support
- https://claude.com/docs/cowork/guide/plugins

OpenAI:
- https://learn.chatgpt.com/docs/plugins
- https://learn.chatgpt.com/docs/developer-commands
- https://learn.chatgpt.com/docs/hooks
- https://developers.openai.com/plugins
- https://developers.openai.com/plugins/build/plugins
- https://developers.openai.com/plugins/concepts/plugins