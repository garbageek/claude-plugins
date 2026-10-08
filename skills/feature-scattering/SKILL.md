---
name: feature-scattering
description: Investigate feature locality, shotgun-change costs, divergent change, and responsibility boundaries using source distribution and optional Git co-change signals. Use when changing one feature requires coordinated edits across unrelated modules. Read-only analysis by default; confirmed findings use the existing audit contract only when ticketization is requested.
---

# Feature Scattering

Find concrete change-locality problems, not every feature mentioned in several files. Use the [deep-review finding contract](../deep-review/SKILL.md) and [public audit contract](../../docs/audit/CONTRACT.md). This is a source-analysis helper, not another lifecycle.

## Inputs and invocation

Establish the repository root, source scope, feature terms (or explicit auto-discovery), and relevant history limit. Read the actual intended boundaries and representative callers before judging a boundary violation. Resolve `AUDIT_PLUGIN_ROOT` from the installed skill using the [invocation contract](../../docs/audit/CONTRACT.md#1-canonical-runtime-invocation), not from a private checkout or an assumed host environment variable. Python 3.10+ and optional Git are required.

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/scatter_scan.py" /path/to/repo --scope src --terms checkout FEATURE_PROMO --git-commits 200 --json
```

Replace the example root/scope/terms with observed inputs. `--scope` accepts repeated repository-relative files/directories; omission means the repository. Omit `--terms` for flag-shaped auto-discovery; `--no-git` disables history. `--json` selects machine output; default is Markdown. Thresholds, directory exclusions, and history limits are available in `--help`. The helper writes only stdout/stderr; do not redirect it into repository artifacts unless requested.

## Read coverage before interpreting signals

Both formats report extension policy (including extensionless files), hidden/excluded paths, oversized/unreadable/binary/symlink files, and actual scanned count. History distinguishes available, unavailable, failed, and disabled; unavailable measurements are null, not zero. Available history is bounded to non-merge commits and may be shallow. Oversized commits are excluded and counted before scope filtering. Co-change includes historical paths that may no longer exist; a current term scan cannot inspect their old contents.

Directory-based module grouping is a locality proxy, not an inferred domain owner. Counts/strengths are ranking signals, not severity, causal coupling, or proof of damage. Empty results mean no match within stated coverage/thresholds, not absence of a problem. Output limits are reported.

## Confirm before classifying

1. Follow term-spread candidates to actual feature fragments and their callers. Record file/line locations and why one change requires coordination.
2. Read representative co-changing commits. Rule out bulk formatting, mechanical renames, generated files, and unrelated changes bundled in one commit.
3. Compare the responsibility model with actual code. A feature legitimately spanning UI/service/storage is not automatically misplaced; a cross-cutting concern with a deliberate mechanism is not uncontrolled duplication.
4. Describe a concrete change and the edits it requires. Identify the smallest useful ownership seam, or explain why the current distribution is intentional. Do not recommend collapsing all layers into one file.

Use descriptive subtypes in the finding body: `scattering` (one feature, many locations), `shotgun-change` (one logical change, many edits), `tangling` (many concerns, one site), `divergent-change` (many independent reasons, one module), uncontrolled cross-cutting logic, execution-flow tangling, or a demonstrated responsibility-boundary violation. Only the first, second, and fanout signals are mechanically scanned; the others require source interpretation. They are **not new audit categories**.

Return consolidated findings and coverage limits directly. No `scatter-audit/`, progress ledger, private ticket template, automatic refactor, or legacy companion CLI. If explicitly asked to record a confirmed maintainability finding, use category **CODE-QUALITY**, retain the subtype in the body, and hand off through the existing discovery runtime with evidence and observable acceptance criteria. Do not alter `audit.py`, role permissions, or exports.
