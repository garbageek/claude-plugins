---
name: local-wiki
description: Build or update a source-backed local repository wiki, validate its navigation, or export a linked Markdown bundle and optional offline static site. Use for implemented-system documentation, not future design or automatic documentation cleanup.
---

# Local Wiki

## Scope and Modes

Choose **inspect/validate**, **author/update Markdown**, **export Markdown**, or
**build/serve HTML** from the request. Inspection and plain validation are
read-only. Creating a wiki does not authorize a site, bundle, local server, or
changes to existing project documentation. Keep generated output separate from
user-maintained documentation; preserve existing narrative on explicit updates.

## Source-backed Authoring

1. Read repository intent, scoped instructions, manifests, real entry points,
   commands, and existing docs. Trace representative handlers, persistence,
   events/jobs, state, and module boundaries instead of inferring them from names.
2. Reconcile discovered capabilities with the relevant directory/package list.
   State meaningful coverage gaps and unknowns. Do not create a survey artifact
   or spawn a fleet of agents; the ordinary workflow is sequential.
3. Choose a proportional table of contents. A small project may need only an
   overview and one workflow page. Add subsystem, API, operations, glossary, or
   contributor pages only when useful. History, statistics, and extensive
   foundation pages are optional, never required sections.
4. Write each chosen page with a title, short summary, source-relative evidence
   in code spans, and links to related wiki pages. Distinguish observed source,
   runtime evidence, inferred explanation, and unresolved behavior. Avoid claims
   of exhaustive coverage or operational success from source inspection alone.
5. In a **dedicated generated wiki directory**, finalize navigation and metadata,
   then validate. Finalization replaces only marked index blocks and generated
   metadata, adding missing indexes; it preserves prose outside those blocks.
   It is a write operation, not part of an inspection-only request.
6. Inspect unresolved links, headings, and important source claims. Report actual
   helper results and limitations; do not mark inferred behavior as reproduced.

Use lowercase kebab-case filenames for newly generated pages and keep individual
pages focused. Split unwieldy pages when useful, not to fill a template. Existing
`.wiki-meta.json` page order is respected; otherwise indexes precede sorted pages.
The metadata is consumed by navigation and validation, not migration bookkeeping.

## Installed Helpers

Python **3.10+** is required. Resolve `SKILL_DIR` to the directory containing this
loaded skill file. It is a shell variable set from the actual installed resource
path, not a universal host-provided variable. Helpers and HTML templates resolve
relative to that installed location; no checkout or editable install is needed.

The following are independent operations; run only those authorized:

```bash
python3 -B "$SKILL_DIR/scripts/local_wiki.py" finalize /path/to/generated-wiki --repo /path/to/repo
python3 -B "$SKILL_DIR/scripts/local_wiki.py" validate /path/to/generated-wiki
python3 -B "$SKILL_DIR/scripts/local_wiki.py" build-markdown /path/to/generated-wiki --out /path/to/wiki-bundle.md
python3 -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
python3 -B "$SKILL_DIR/scripts/local_wiki.py" build-site /path/to/generated-wiki --out /path/to/wiki-site
python3 -B "$SKILL_DIR/scripts/local_wiki.py" serve /path/to/wiki-site --port 8765
```

`finalize`, `validate`, and `build-markdown` use only the standard library.
Installing dependencies is needed only for requested HTML rendering and requires
permission to change the selected Python environment. The optional renderer uses
Jinja2 and markdown-it-py; it does not fetch browser scripts or invoke formatters.
Mermaid remains readable fenced source offline rather than a remotely rendered
diagram. The site contains local navigation, search JSON, CSS, and JavaScript.
Search needs HTTP access to the site; the explicit `serve` operation runs in the
foreground until interrupted. A generated file is not evidence of a live server.

## Output and Validation Boundaries

- The Markdown bundle must be a new file outside the wiki; existing output is
  refused. Preserve page anchors and relative source evidence. Attachment links
  are rebased to the original wiki files; move those files with the bundle when
  sharing it, or explicitly choose a different asset delivery strategy.
- Site output must be outside and not an ancestor of the source wiki. An existing
  directory is replaceable only when marked by this renderer (`.droid-wiki-site`).
  Its basename never authorizes deletion. Never add a marker to unrelated content
  to bypass refusal; choose a new destination. Marked site directories are wholly
  generated, so do not store manual edits there.
- Plain validation checks structure, metadata consistency, and inline local-link
  file targets. It is not a full Markdown dialect/fragment validator or proof of
  the prose. Review heading fragments, reference-style links, images, and browser
  navigation separately. The optional `validate --auto-fix` rewrites headings and
  some links; run it only when that edit is explicitly authorized.
- A nonzero helper result is a failure, not a completed wiki. Preserve partial
  output for inspection; do not delete source or unrelated directories to retry.

Return the requested output paths, actual commands/results, and remaining gaps.
Do not generate a companion report, automatic statistics, extra archive, or
publication workflow.
