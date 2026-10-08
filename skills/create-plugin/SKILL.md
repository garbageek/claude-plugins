---
name: create-plugin
description: Use when the user requests a new Claude Code or Codex plugin, a reusable workflow packaged for either or both hosts, or creation of a private plugin through the connected Plugin Creator backend.
---

# Create plugin

Create a focused plugin that solves the user's actual workflow. Do not start from
a generic feature checklist or add components merely because plugins support them.
Read the shared [platform contracts](../../references/plugin-authoring.md) before
authoring manifests or claiming host compatibility.

## Target and delivery

Infer the target from the request: **Claude**, **Codex**, or **both**. Default a new
unspecified target to both; this is an authoring choice, not a platform requirement.
Choose source/project/archive delivery separately from backend publication. A request
for an archive or repository addition does not authorize creating a hosted plugin.
Ask only when a missing detail materially changes the required behavior or destination.

Local authoring needs source/file tools, not Plugin Creator. For a requested hosted
creation, discover the separately connected backend's actual tools and their schemas.
If unavailable, prepare the usable source/package and report the blocked publication;
do not invent an MCP endpoint, app mapping, plugin ID, or successful upload.

## Principles

- Preserve the requested scope and behavior over generalized best practices.
- Prefer the smallest structure that fully supports the workflow: one skill per
  distinct job, with common references or runtime only when actually shared.
- Keep skills under `skills/<skill-name>/SKILL.md`, with matching frontmatter name
  and a precise activation description. Share them across hosts rather than forking.
- Add apps, MCP servers, hooks, agents, assets, and compatibility files only when
  they provide a required capability. Never fabricate credentials, tools, or assets.

## Workflow

1. Determine the real jobs, authoritative inputs, required result, selected hosts,
   and destination. Read supplied material and existing repository instructions.
2. Check the intended source path/identity for a collision; use backend discovery
   only for a requested backend target. Do not silently overwrite another plugin.
   Route an actual update to [update-plugin](../update-plugin/SKILL.md).
3. Select the Codex format using the shared platform contract: portable root
   `plugin.json` for portable components, or native `.codex-plugin/plugin.json`
   when the required host capabilities need that loader. For Claude, author
   `.claude-plugin/plugin.json`. For both, synchronize the selected manifests'
   identity/version/description and share one `skills/` tree. Do not insert a root
   portable manifest into a native package without checking the loader consequences;
   adding a second manifest does not make the two formats merge.
4. Write complete instructions: when each skill applies, required inputs, concrete
   actions, constraints, failure behavior, and expected result. State missing-tool
   behavior without replacing the user's requested capability with a weaker one.
5. Identify real runtime dependencies. Adapt MCP/hook/agent contracts per host when
   needed; merely adding manifests is insufficient for runtime parity. Declare a
   verified skill dependency in `agents/openai.yaml` only when useful. Registered
   app mappings and separately connected host tools remain explicit dependencies.
6. Validate the effective package and supporting files. Run the existing repository
   checker when integrating there. Record structural versus actual host results;
   do not require a backend release to call a source/archive deliverable complete.
7. Deliver to the requested destination. In an existing toolkit, add the requested
   skills to its shared plugin unless a separate installable product is requested
   or justified by actual consumer requirements. Different skill purposes alone
   do not require separate plugins. Update only affected registration and usage.
   For an archive, include the complete requested plugin or project under a new
   versioned filename for revisions. Do not publish, push, or merge implicitly.
8. Only for requested backend creation, package exactly one compatible plugin and
   call `create_plugin` with its actual absolute archive path. The backend chooses
   the active workspace, or personal scope without one, and creates a private plugin.
   Do not invent a scope-selection argument or claim Claude publication from this.

## Readback and output

For a hosted result, retain the returned backend ID and release ID. Inspect the
created metadata/file inventory through available readers before claiming checked
content. Separate a successful creation from unavailable or concurrently changed
readback; do not create a duplicate merely because inspection failed.

Report the actual result: source/archive path and included skills/targets, or the
backend's returned version, release ID, status, and clickable `plugin_url`. State
material runtime/host checks not performed. Supply only the requested deliverables;
no automatic companion reports or empty scaffold files.
