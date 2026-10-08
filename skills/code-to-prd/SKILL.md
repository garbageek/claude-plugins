---
name: code-to-prd
description: Reverse-engineer a frontend, backend, or mixed codebase into an evidence-backed Product Requirements Document. Use when documenting existing routes, user flows, APIs, data contracts, permissions, background work, and observable behavior without inventing missing product intent.
---

# Code to PRD

Reverse-engineer an existing frontend, backend, or mixed codebase into an evidence-backed Product Requirements Document.

## Required Reference Routing

Load only the references needed for the current stage, but do not skip the required stage reference:

| Stage | Required reference |
|---|---|
| Framework detection and source inspection | [framework patterns](references/framework-patterns.md) |
| Final validation before delivery | [quality checklist](references/prd-quality-checklist.md) |

For mixed or monorepo projects, apply the framework reference independently to every detected application/package. Never select one “primary” framework and ignore the others.

## Modes and Installed Helpers

Choose the requested mode: **analyze only**, **create PRD**, or **update existing PRD**.
An inventory request never authorizes scaffolding. Updating an existing PRD is a
source-backed document edit, not a scaffolder rerun; preserve manual work and the
existing organization. Generate only the requested output scope.

Helpers require Python 3.10+ and the standard library. Resolve `SKILL_DIR` to the
actual directory containing this loaded `SKILL.md`; it is a shell variable you
set from the installed resource path, not a required host environment variable.
Do not look for a development checkout or another globally installed skill.

## Workflow

### 1. Build the inventory

For an inventory-only request, run only the selected analyzer command. Stdout is the default; `-o` writes only the explicitly chosen inventory file:

```bash
python3 -B "$SKILL_DIR/scripts/codebase_analyzer.py" /path/to/project
python3 -B "$SKILL_DIR/scripts/codebase_analyzer.py" /path/to/project -f markdown
# Only when saving the inventory was requested:
python3 -B "$SKILL_DIR/scripts/codebase_analyzer.py" /path/to/project -o analysis.json
```

An invalid/unreadable root returns nonzero with a stderr diagnostic. Evidence paths are relative to the analyzed repository (`project.root` is `.`); retain the chosen root in the current working context. Treat the output as a starting inventory, not as product truth. It deliberately separates:

- frontend pages;
- inbound backend endpoints;
- outbound API calls;
- models, schemas, and DTOs;
- enums and constants.

Review every detected source location and resolve duplicate or generated routes in context. Resolve every endpoint marked `unresolved_prefix` before treating its path as complete. This commonly includes Django `include()`, DRF router actions, Express router mounts, and runtime-composed prefixes.

### 2. Create the evidence workspace

Only when PRD creation is requested. The destination must be absent or empty.
A populated directory is refused with a nonzero result; no existing files are
deleted or replaced. There is no force/merge mode. An interrupted write may leave
new partial output: inspect it, do not automatically delete it to rerun.

```bash
python3 -B "$SKILL_DIR/scripts/prd_scaffolder.py" analysis.json -o prd/ -n "Project Name"
```

The generated files contain `[TBC]` evidence gaps. They are intentionally not presented as a completed PRD.

### 3. Perform targeted source passes

For every page, inspect:

- rendered regions, labels, controls, tables, charts, modals, drawers;
- defaults, validation, conditional visibility, loading, empty, error, and permission states;
- navigation calls, route parameters, shared state, refresh behavior;
- outbound API calls and response mapping;
- i18n labels and enum-to-label mappings.

For every backend endpoint, inspect:

- method and full composed path;
- path/query/header/body contract;
- serializer/DTO/schema validation;
- guards, decorators, middleware, permissions, ownership checks;
- service calls, database reads/writes, transactions, events, jobs, and external calls;
- status codes, error mapping, idempotency, retries, and environment-dependent behavior.

Perform separate inventory passes for:

- middleware and global guards;
- background tasks, queues, cron, and schedulers;
- migrations and database constraints;
- Django admin configuration;
- environment/configuration branches;
- serializers, forms, validators, and generated API schemas.

### 4. Write in product language

Describe user-visible or externally observable behavior. Keep implementation detail only when it changes product behavior or defines a contract.

Label **extracted source facts**, **inferred product meaning**, and **unknown behavior** separately. A generated route title is a naming suggestion, not a confirmed business requirement. Do not treat static API-call detection as proof of a live integration. Use `[TBC]` when evidence is incomplete. State what was observed and what remains unresolved. Do not invent business meaning.

### 5. Validate before delivery

Load and execute [quality checklist](references/prd-quality-checklist.md). Every checked item must have source evidence. Unresolved items remain explicitly marked `[TBC]`; they must not be silently treated as complete.

## Output Structure

```text
prd/
├── README.md
├── pages/
├── endpoints/
└── appendix/
    ├── api-inventory.md
    ├── enum-dictionary.md
    ├── model-dictionary.md
    └── page-relationships.md
```

## Tool Limits

The analyzer is stdlib-only, package-scoped, and intentionally conservative. Static extraction cannot prove runtime behavior, authorization semantics, generated routes, middleware ordering, or business intent. The manual evidence pass is mandatory.
