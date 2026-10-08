---
name: inspect-plugin
description: Use for read-only inspection of a Claude Code or Codex plugin from source, an archive, or an accessible Plugin Creator release, including structure, compatibility, integrations, release history, and change assessment.
---

# Inspect plugin

Inspect first, change nothing unless the user separately asks for an edit. Read the
shared [platform contracts](../../references/plugin-authoring.md) for host-specific
manifest authority and compatibility boundaries.

## Select the actual source

For an attached archive or local repository, inspect that exact source; no Plugin
Creator connection is required. Read the complete inventory and relevant source,
not only filenames. Do not replace a supplied snapshot with a live branch without
request, and do not assume archive suffixes establish freshness. Resolve a repository
URL through the available source connector when appropriate.

For a hosted plugin, discover the backend's available tools first. Installing this
package does not connect them. Resolve the exact backend ID from returned metadata
or supported discovery; a display name, GPT ID, URL slug, or local file ID is not a
plugin ID. Preserve its spelling/case/prefix. Do not treat absence from one listing
as proof the plugin does not exist or that edit access was denied.

## Current source

1. For metadata-only hosted questions, use `get_plugin_metadata`. For file content,
   call `get_plugin_files` first without `read_paths`, then follow every `next_offset`
   needed for the requested inventory. Do not guess unread paths.
2. Read relevant text in batches of at most 20 exact `read_paths` from that inventory.
   Use `get_owned_plugin_archive` for binary, oversized, or unavailable content. For
   full-plugin inspection, finish the inventory before describing all components;
   for focused work, state the inspected scope. Local sources follow the same
   completeness rule without a backend API or release guard.
3. Retain `current_release_id`. If it changes between reads, refresh against a
   consistent release; do not combine different releases into a claimed snapshot.
4. Inspect the manifests actually present: portable root `plugin.json`, native
   `.codex-plugin/plugin.json`, and/or `.claude-plugin/plugin.json`, plus skills,
   links/assets, and relevant MCP/hooks/apps. Check which format the target host
   selects; do not assume a native manifest is always a fallback or that settings
   merge. Report drift without editing.
5. Compare selected host capabilities, launch paths, dependency availability, and
   output/action boundaries. Two manifests do not prove identical runtime behavior.
6. Distinguish confirmed source facts, inferred behavior from instructions, actual
   execution evidence, and unavailable checks. Do not invent a defect from a generic
   pattern or claim live loading from a valid archive.

## Release history

Only query historical releases when the user asks about previous versions, release
history, regression origin, or comparison. Use `list_plugin_releases`, following
`next_cursor` as needed even through empty pages. Results are in attachment order
and may include unpublished releases; do not equate order with version or publication
chronology. Local Git history or supplied older archives are separate evidence.

Retrieve only the needed historical releases, using returned release IDs with
`get_owned_plugin_archive`. Its downloaded release describes that snapshot; plugin
metadata can describe the current release. Downloading history does not restore it.
For a named comparison, use the exact requested release. For regression analysis,
inspect the minimum relevant set to locate unaffected/affected behavior, distinguishing
source changes from runtime regressions proven to have shipped.

## Output

Prefer a compact summary: identity/version, selected hosts, skills, integrations,
authoritative files, useful constraints, and concrete issues with source locations.
Preserve the requested terminology and level of detail. Do not manufacture findings,
modify source, write a report file, publish, restore, or run mutating helpers merely
because inspection was requested.
