# Claude and Codex package contracts

Shared by create, inspect, and update. Use current official documentation for
platform behavior and the live tool schema for backend operations. The defaults
below are this creator's authoring choices, not additional platform requirements.

## Target and destination are separate

Select **Claude**, **Codex**, or **both** independently of whether the result is
source files, an archive, a repository change, or a Plugin Creator backend release.
For a new plugin with no narrower target, default to both. For an update, preserve
the existing target set unless the user requests conversion or another host.

Source authoring, inspection, and packaging work with local files or supplied
archives in either host. They do not require the Plugin Creator backend. Installing
this package does not connect that backend, GitHub, or any other service. Discover
available tools before a live operation. When a connection is missing, use the
host's supported discovery/setup path; continue useful source work without
claiming backend access or publication. Never invent an endpoint or an app mapping.

Creating source is not publishing, registering a marketplace is not installing,
and a backend release is not a Git push, a Claude account upload, or public-directory
approval. Perform only the destination-changing operations the user requested.

## Minimum package for each target

| Target | Required by this authoring profile | Component source |
|---|---|---|
| Claude | `.claude-plugin/plugin.json` | Shared `skills/<name>/SKILL.md` and necessary support files at plugin root |
| Codex | Portable root `plugin.json`, or supported native `.codex-plugin/plugin.json` when client capabilities require it | The same `skills/`; MCP format follows the chosen manifest |
| Both | `.claude-plugin/plugin.json` plus the selected Codex manifest | One copy of each skill, reference, asset, and runtime; adapters only where contracts differ |

For a skills-only portable dual package, use this minimum tree; create no empty component directories:

```text
plugin-name/
├── plugin.json
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── workflow-name/
        └── SKILL.md
```

Root `plugin.json` uses `$schema` set to
`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`. Keep portable `name`,
string `version`, `description`, and author information there. Put OpenAI
presentation in `extensions.com.openai.interface`, not in invented portable keys.
Use only known author information and actual asset paths; do not fabricate metadata
to fill optional fields. For a registered package, keep its effective Codex interface `category`
consistent with the OpenAI marketplace entry.

The Claude manifest uses its documented fields, with the same identity, version,
and description for a dual package. Do not paste `extensions.com.openai` into it.
Component paths refer to the plugin root, not the manifest directory. Explicit
manifests, nested skills, and synchronized identity are this repository's chosen
conventions; Claude also supports other documented layouts.

Prefer lowercase kebab-case plugin/skill names and SemVer for new packages. Validate
the target's real constraints; portable names can permit forms beyond that default,
and a version string is not universally required to be SemVer. Preserve a valid
existing scheme unless changing it is part of the request. Store current release
numbers only where package consumers need them, not in README tables or headings.

When `extensions.com.openai` is an object, it replaces the entire
`.codex-plugin/plugin.json` overlay for OpenAI settings; they are not merged.
Do not add that overlay to a new portable package by default. A supported legacy-only
package is not broken solely for lacking a portable root; convert it only when the
requested target or change requires that. For an existing package, preserve the
overlay if required; before removing it, retain any needed effective
settings in their authoritative location and update references. If retained,
synchronize duplicated identity and interface data, including `defaultPrompt`
value/type/order. Removing it from a backend release needs `delete_paths`.

### Select the loader for required capabilities

A portable root is a default, not a requirement to discard working native
integration. Current Codex source skips hook loading for `AgentPlugin` but loads
hooks for its native/legacy manifest. When required hooks rely on that native
path, use `.codex-plugin/plugin.json` without a portable root `plugin.json`, select
the hook and native MCP config explicitly, and verify the installed host. Adding
an ignored compatibility overlay next to a portable root does not change the
selected format. Preserve a working format during updates; never add a root
manifest mechanically and claim the same runtime behavior. See the
[Codex loader](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs).

## Shared skills and runtime-dependent features

Each `SKILL.md` has matching directory/frontmatter `name` and a precise activation
`description`. Keep portable instructions independent of Claude slash-command
spelling, hardcoded tool IDs, or one host's environment variables. Give supporting
files real relative links. Resolve helpers from the installed skill/plugin and
consumer inputs from the chosen project; do not write working state in plugin cache.

`agents/openai.yaml` is optional skill interface/dependency metadata, not a runnable
subagent. Add it only for an actual interface/dependency need and check its schema.
Omit `policy.products` unless product filtering is explicitly needed; do not invent
product values. Claude-only frontmatter, dynamic command injection, or tool policies
must not be presented as enforced behavior in Codex.

Add integrations only when the workflow requires them:

| Feature | Adaptation boundary |
|---|---|
| MCP | Claude uses `.mcp.json` or supported manifest configuration. Native Codex can select a separate config with `mcpServers`; portable Codex uses root `mcp.json` with the Agent Plugins schema and explicit transport types. Do not copy a Claude `http` transport unchanged as portable `streamable-http`. Share the real server and verify each launcher contract. |
| Hooks | Use the documented host event/input/output contract and shared executable logic where possible. Native Codex selects its adapter through manifest `hooks`; portable documentation describes `extensions.com.openai.hooks`, but the current AgentPlugin loader may skip it. Explicit selection replaces Codex default hook discovery, not Claude's additive hook loading. Check the selected loader, trust, tool names, and payloads in the actual host. |
| Agents and commands | Preserve Claude agents/commands when used. Select supported Codex skills/subagents or MCP operations for their behavior; copying Markdown or renaming a role does not reproduce enforced permissions or independent execution. |
| Host apps | An OpenAI `.app.json` references registered server/app mappings; it does not connect the same service in Claude. Discover a real equivalent integration or state the unavailable capability. |

Check launcher quoting, path substitution, runtime dependencies, workspace selection,
and each relevant failure/denial path. A prompt-only shared package needs no hook,
MCP wrapper, daemon, or generator. A required feature that lacks an adapter remains
an explicit compatibility gap; do not silently remove it and label the result fully
cross-platform. Hooks are not a universal filesystem boundary.

## Repository and archive delivery

Read the selected repository's manifests, conventions, instruction scope and
validator. A marketplace can point at one root plugin or several plugin folders;
there is no one-plugin-per-skill requirement. This repository installs one toolkit
at `./`, with shared skills. Add workflows to that toolkit unless the user requests
a separate product. Do not recreate the removed standalone-product directories.

- Claude `.claude-plugin/marketplace.json`: this repository's `source` is `./`.
- Codex `.agents/plugins/marketplace.json`: its source is
  `{"source":"local","path":"./"}`. Other repositories can legitimately use
  `./plugins/<name>` or another contained plugin root. Preserve their established
  organization, install/authentication policy, and interface category.

These paths are relative to the marketplace root, not to the registry directory.
Keep the existing marketplace identity and unrelated entries. Update affected
README usage, without duplicating the catalog or adding verification-date banners.
Do not silently edit GitHub main, merge a PR, publish, or change account settings.

A Plugin Creator backend upload contains exactly one plugin, not a collection of
separately packaged plugins. A repository whose root is itself one plugin can use
that root as its package; still check the backend's accepted format. A requested
project archive includes the complete project rather than only changed files. ZIP entries may be at the plugin root or under
one containing plugin directory. Include every referenced runtime file and binary
asset required by the chosen delivery mode. Omitted backend files survive an
overlay update; omitted archive files do not magically exist for its recipient.
Exclude caches, nested packaging copies, and unrelated work files. Inspect archive
paths and links before extraction; do not follow them outside the working area.

For a revised downloadable artifact, increment its actual filename version. Ignore
parenthetical duplicate suffixes such as `(1)`; do not return changed bytes under
the input filename. Preserve stable filenames inside a repository when consumers
require them. Do not create a migration report, manifest inventory, or per-skill
archive unless it is itself a requested output.

## Validation and delivery claims

Validate against the selected schemas and the owning repository's existing checker.
For Claude, use `claude plugin validate <plugin-directory>` when available; its
`--strict` mode additionally rejects warnings. Do not claim this ran when the CLI
is absent. Check JSON/YAML, skill identity/description, local links, dependencies,
manifest agreement, and the effective package after a backend overlay/deletion.
Do not create a new test suite unless requested.

Inspect generated instructions for unimplemented guarantees and run relevant
helpers in an isolated workspace when execution is authorized. For claimed host
behavior, separately check actual installation/discovery, skill invocation, MCP
startup, hooks/trust and project-write boundaries as applicable. Structural checks,
manual execution, backend readback, and installed-host acceptance are separate
results. Report unperformed checks explicitly; do not invent success or publish
again to compensate for an unavailable readback.

## Official sources

- [Portable packaging, registries, MCP, and OpenAI metadata](https://developers.openai.com/plugins/build/plugins)
- [Claude plugin manifest and component paths](https://code.claude.com/docs/en/plugins-reference)
- [Claude skills and host-specific extensions](https://code.claude.com/docs/en/skills)
- [Codex skill metadata](https://learn.chatgpt.com/docs/build-skills)
- [Codex hook events, payloads, and trust](https://learn.chatgpt.com/docs/hooks)

Backend operation names and arguments in these skills describe the separately
connected **Plugin Creator**. Read the actual available tool schema before calling
it; they are not portable plugin fields or a promise of a Claude API.
