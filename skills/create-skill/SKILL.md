---
name: create-skill
description: Create, edit, evaluate, or optimize a reusable Agent Skill (SKILL.md) for Claude Code, Codex, or both. Use for standalone skills, skill instructions inside an existing plugin, skill trigger descriptions, evaluations, benchmarks, and .skill packaging. Route whole-plugin creation and release management to create-plugin or update-plugin instead.
---

# Create Skill

Read and apply [the delivery contract](../../references/delivery-contract.md) within this skill's scope and authorization.

Create or improve **Agent Skills** as independent, reusable workflows. The user
selects the task and delivery; this skill owns the `SKILL.md`, supporting files,
and optional evidence-driven iteration. Do not turn skill-only requests into a new
plugin, host installation, or hosted release.

This skill adapts the user-supplied Apache-2.0 `skill-creator` to the shared Claude
Code and Codex skill layout. It preserves the supplied evaluation/report helpers,
but does **not** claim the Claude CLI trigger evaluator can measure Codex skill
discovery. Read [host distinctions](references/hosts.md) when choosing a runner.

## Scope and routing

- **Create a standalone skill:** produce `<skill-name>/SKILL.md` with resources
  only when needed, or place it at `skills/<skill-name>/SKILL.md` inside the
  selected existing toolkit. Default an unspecified target to both Claude and
  Codex, subject to the actual host/tool capability.
- **Improve an existing skill:** read the current skill and referenced support
  files first; preserve its name, unrelated behavior, and invocation boundaries.
  Record a baseline snapshot only if comparative evaluation is requested.
- **Create or replace a plugin:** route package design to
  [create-plugin](../create-plugin/SKILL.md) and source/release updates to
  [update-plugin](../update-plugin/SKILL.md). Creating one skill does not
  authorize publishing/releasing an entire plugin.
- **Install or enable a skill/plugin:** follow
  [install-agent-plugins](../install-agent-plugins/SKILL.md) if installation is
  requested. Source packaging is not proof of installation or discovery.

## 1. Capture the job

From the request and supplied material, determine:

1. What job the skill performs and what differentiates it from existing skills.
2. Triggering language: *when* it should run, including near-misses and exclusions.
3. Inputs, dependencies, actions, constraints, output files, and failure behavior.
4. Target host(s), filesystem destination, and whether the user wants evaluation,
   packaging, or installation. Use existing details; ask only when the missing
   choice materially changes the artifact.

If an upstream skill, archive, or repository is supplied, **adapt that source**;
do not replace it with a generic template. Do not silently introduce project
names, credentials, or private workflow specifics into an otherwise reusable skill.

## 2. Write a focused SKILL.md

Use a single root `SKILL.md` per skill, with YAML frontmatter:

```yaml
---
name: example-skill
description: Use when the user needs to ...; creates/updates ... .
---
```

The directory and frontmatter name must match; prefer lowercase kebab-case.
Write all trigger criteria in `description`, keeping it concrete and distinct
from neighboring skills. The body must explain what to do and why, with:

- Authoritative inputs, where to find them, and actual available tools.
- Sequenced actions and decisions, not merely a capabilities list.
- Exact expected deliverables and preservation constraints.
- Failure, missing-data, unsupported-host, and missing-tool behavior.
- Links to supporting resources by valid **relative paths**.

Use `references/` for substantive secondary detail, `scripts/` for useful
repeatable operations, `assets/` for resources used in outputs. Avoid empty
scaffolding, duplicated host-specific skill trees, and automatic side effects.
Skills should remain discoverable and actionable without needing to read every
bundled file. Follow the existing package's manifest authority and conventions.

## 3. Validate and optionally package

Use the supplied portable helpers from this skill's directory (`SKILL_DIR`):

```bash
cd "$SKILL_DIR" && python -m scripts.quick_validate /absolute/path/to/example-skill
cd "$SKILL_DIR" && python -m scripts.package_skill /absolute/path/to/example-skill /absolute/path/to/output
```

`quick_validate.py` and `package_skill.py` require Python 3 and PyYAML; they
validate portable metadata and create a ZIP-format `.skill` archive. They are
**structural checks**, not runtime discovery or proof of correct behavior.
Within an existing plugin, also run its actual packaging validation if available.
Do not package unrelated plugin files into a standalone `.skill` artifact.

## 4. Optional real evaluations and iteration

Skip evaluations if they were not requested or would incur an unwanted runtime
or billing cost. For changes with measurable outcomes, reuse existing evaluation
cases rather than inventing a test suite. Cases can use the supplied
[case schema](references/schemas.md): `evals/<case-name>/prompt.md`,
`case.yaml`, optional `graders/`, and `files/`. Avoid writing assertions for
purely subjective quality; use human review instead.

A measured iteration is:

1. Run representative tasks with the skill, and optionally a baseline without
   it or with the prior version. Keep input prompts and files identical.
2. Store the outputs and exact execution evidence in a separate workspace;
   never overwrite the source skill just to create an evaluation run.
3. Review outputs first. If evidence supports an improvement, change the smallest
   relevant part of the instructions or helper. Compare again only on request.
4. Report what was **actually** run, outcome differences, unknowns, and costs.
   Do not invent grades, token metrics, or passing evaluations.

**Cross-host functional evaluation:** `scripts/run_task_evals.py` can run cases
with an installed `claude` or `codex` CLI. It creates isolated workspaces with
and optionally without the skill and writes reviewable outputs, without claiming
to measure automatic trigger accuracy. This command executes real model runs:

```bash
cd "$SKILL_DIR" && python -m scripts.run_task_evals --host codex --skill-path /absolute/path/to/example-skill --workspace /absolute/path/to/workspace --baseline
```

Use `--host claude` for the Claude CLI, or `--dry-run` to inspect planned runs
without invoking an agent. This runner requires the selected authenticated CLI
and a filesystem supporting its project skill layout; inspect the tool's help
and the host's permissions before real calls. Compare only evidence-backed
results. The runner does not itself grade outputs.

**Claude-specific trigger evaluation:** The preserved `scripts/run_eval.py`,
`run_loop.py`, and `improve_description.py` call `claude -p` and inspect Claude
skill invocation. Run them only on Claude Code when the executable and needed
permissions exist and the user explicitly asks for trigger optimization. See
[host distinctions](references/hosts.md). These scripts **must not** be used to
claim a Codex trigger score; Codex's skill selection needs host-native evidence.

For completed runs, the original cross-host-capable review tools are available:

```bash
python "$SKILL_DIR/eval-viewer/generate_review.py" /absolute/path/to/workspace/iteration-1 --static /absolute/path/to/review.html
cd "$SKILL_DIR" && python -m scripts.aggregate_benchmark /absolute/path/to/workspace/iteration-1 --skill-name example-skill
```

Only aggregate after `grading.json` exists for runs to be scored. The viewer
can show ungraded outputs. Grading agents (`agents/grader.md`, `analyzer.md`,
`comparator.md`) are **instructions** for an available agent, not installed
subagents or an automatically running workflow.

## 5. Improve description triggering when justified

Separate **task quality** from **trigger accuracy**. Create realistic positive,
negative, and borderline queries for the selected host; do not overfit to a
single repository or a few phrases. The supplied `assets/eval_review.html`
provides a local human-review template. For Claude Code, the preserved scripts
can automate trigger evaluation and description proposals. For Codex, review
actual host discovery/invocation traces or compare manual examples; do not
pretend that text matching or explicit skill injection measures auto-triggering.

## Output

Deliver the requested `SKILL.md`, directory/archive or edit to the authorized
source. Summarize its trigger, target hosts, bundled helpers, and any limitations
of execution. Do not auto-publish, install, push, merge, or create additional
reports. If a requested destination is inaccessible, provide the complete
source package and state exactly what was not changed.
