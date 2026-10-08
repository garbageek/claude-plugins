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
| Codex | Root `plugin.json` with the Agent Plugins schema | The same `skills/`; optional root `mcp.json` |
| Both | Root `plugin.json` plus `.claude-plugin/plugin.json` | One copy of each skill, reference, asset, and runtime; adapters only where contracts differ |

For both, use this minimum tree; create no empty component directories:

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
to fill optional fields. For this marketplace, include an interface `category`
matching the OpenAI registry entry.

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
| MCP | Claude uses `.mcp.json` or supported manifest configuration. Portable Codex uses root `mcp.json` with the Agent Plugins MCP schema and explicit transport types. A remote Claude `http` transport is not copied unchanged as portable `streamable-http`. Share the real server, not an assumed schema. |
| Hooks | Use the documented host event/input/output contract. Prefer separate configurations pointing to common executable logic where possible. Codex can select an adapter through `extensions.com.openai.hooks`; an explicit selection replaces default hook-file discovery. Check trust, tool names, and patch payloads in the actual host. |
| Agents and commands | Preserve Claude agents/commands when used. Select supported Codex skills/subagents or MCP operations for their behavior; copying Markdown or renaming a role does not reproduce enforced permissions or independent execution. |
| Host apps | An OpenAI `.app.json` references registered server/app mappings; it does not connect the same service in Claude. Discover a real equivalent integration or state the unavailable capability. |

Check launcher quoting, path substitution, runtime dependencies, workspace selection,
and each relevant failure/denial path. A prompt-only shared package needs no hook,
MCP wrapper, daemon, or generator. A required feature that lacks an adapter remains
an explicit compatibility gap; do not silently remove it and label the result fully
cross-platform. Hooks are not a universal filesystem boundary.

## Repository and archive delivery

Read the selected repository's manifests, existing plugin conventions, instruction
scope, and validator before editing. In this repository, plugins live under
`plugins/<name>/`. Register only the requested products:

- Claude `.claude-plugin/marketplace.json`: entry `source` is `./plugins/<name>`.
- Codex `.agents/plugins/marketplace.json`: entry `source` is the object
  `{"source":"local","path":"./plugins/<name>"}`. Preserve the repository's
  install/authentication policy and match the plugin interface category.

These paths are relative to the marketplace root, not to the registry directory.
Keep the existing marketplace identity and unrelated entries. Update affected
README usage, without duplicating the catalog or adding verification-date banners.
Do not silently edit GitHub main, merge a PR, publish, or change account settings.

A Plugin Creator backend upload contains exactly one plugin, not the whole
marketplace. A requested project archive contains the complete project instead;
these are different deliverables. ZIP entries may be at the plugin root or under
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
