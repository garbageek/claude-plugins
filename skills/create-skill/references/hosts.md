# Host-specific evaluation and packaging

## Shared format

Both Claude Code and Codex can use the same `skills/<name>/SKILL.md` and portable
resources when a plugin or project installs them according to its own loading
contract. A valid archive is not proof that either host discovered the skill.

## Functional quality evaluation (Claude and Codex)

`scripts/run_task_evals.py` runs cases from a target skill's `evals/` directory
in temporary project workspaces. For each case, it places the skill in the host's
project skill directory (`.claude/skills` or `.agents/skills`), invokes the
selected CLI, stores its final response and generated files, and optionally
runs an otherwise comparable baseline with no skill. A user-supplied input
file belongs under `evals/<case>/files/`. Cases without input files also work.

- Claude: `claude -p` (JSON output) with current configured permissions.
- Codex: `codex exec --json --skip-git-repo-check --sandbox workspace-write`
  with current configured permissions. This executes code in an isolated
  workspace, not in the original skill/project.

The runner cannot force a model to choose a skill automatically. If it is
not loaded, the resulting run is still usable as execution evidence, but must
not be presented as proof of successful skill triggering.

No CLI is bundled. The user must supply installation, authentication, runtime
permissions and any billing for the selected host. Check `--help` on the actual
executable when flags may differ.

## Claude Code-specific triggering scripts

The original scripts below depend specifically on Claude Code's CLI and message
format. They are preserved to maintain functionality and source compatibility:

- `scripts/run_eval.py`: tests whether Claude uses a synthetic command skill.
- `scripts/run_loop.py`: evaluates and iteratively improves descriptions using
  the Claude CLI.
- `scripts/improve_description.py`: proposes descriptions by calling Claude.

These are **not** accurate measures of Codex triggering. They also do not test
whether an actual plugin skill is recognized end-to-end under all host configs.

## Review and benchmark helpers

`scripts/aggregate_benchmark.py`, `scripts/generate_report.py`,
`eval-viewer/generate_review.py`, `eval-viewer/viewer.html`, and
`assets/eval_review.html` process results and review evidence without
specifically requiring either CLI. `--static` produces reviewable HTML when
no browser/server is available. Aggregation requires actual grading results;
never manufacture grades or token counts just to populate a chart.

## Packaging

`python -m scripts.quick_validate TARGET` and
`python -m scripts.package_skill TARGET OUTPUT_DIR` run from this skill's
root, require PyYAML, and operate on **one skill**, not an entire plugin.
For plugin integration use the surrounding toolkit's manifests, versioning,
and own validation as separate steps.
