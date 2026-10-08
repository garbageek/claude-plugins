# Discovery and Retention

## Working Boundary

Identify the requested host, working directory, repository root, and target file
before drafting. Use existing repository/tool evidence to resolve these. An
unavailable host configuration is an explicit unknown, not permission to invent
an instruction-loading model. Inspect relevant ancestor instruction files when
host discovery requires it; do not crawl unrelated parent repositories.

Keep two questions separate: **which instructions the host loads** and **which
repository claims current code supports**. A prose rule may express intended
policy while code currently violates it. That is drift to explain, not automatic
authority to discard the rule. The user's requested policy is not overridden by
an executable merely because the executable does something else.

## Host Loading Reference

The following summarizes documented host behavior, not requirements invented by
this plugin. Recheck the linked official sources when the installed
host/version/configuration differs or loading is uncertain.

### Claude Code

Direct `AGENTS.md` loading requires v2.1.277+ and an enabled implementation. By
default, `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in the working
directory or ancestors selects Claude instructions instead of AGENTS files.
Otherwise ancestor/current `AGENTS.md` and `.claude/AGENTS.md` load; descendant
AGENTS files can load on reads when no local Claude counterpart takes precedence.
User/managed instructions and `.claude/rules/` do not trigger that exclusion.
The Project instructions setting can select another behavior. An explicit
`@AGENTS.md` import is an option when needed, not a universal bridge requirement.
Claude does not automatically load `AGENTS.local.md`, `AGENTS.override.md`, or
instructions under `.agents/`. Confirm the active file list in the host; do not
change settings or generate a bridge merely to normalize a repository.

Source: [Claude instruction loading](https://code.claude.com/docs/en/memory).

### Codex

At startup, Codex reads the first non-empty global `AGENTS.override.md` or
`AGENTS.md` under its configured home. It then walks project root to working
directory, choosing at most one non-empty file per directory: `AGENTS.override.md`,
then `AGENTS.md`, then configured fallback filenames. More local guidance follows
and overrides earlier conflicting guidance. Without a discovered project root,
only the working directory is checked. The default combined instruction budget
is 32 KiB, configurable through `project_doc_max_bytes`; fallback names are also
configurable. Do not assume a file below the launch directory has already loaded,
or treat `CLAUDE.md`/`AGENTS.local.md` as automatically selected without a configured
mechanism. Confirm the actual home, working directory, and discovery settings.

Source: [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

## Evidence Discovery

Read the existing target in full first, then its relevant scope chain. Survey
manifests/workspace declarations, runtime pins, task runners, CI, configuration,
generated-file boundaries, and existing documentation. Trace representative
entrypoints and multi-file responsibilities only when they change a proposed
rule. Recognize code, configuration, documentation, and data repositories without
forcing all of them into a software build template. Empty repositories do not
justify fabricated commands or conventions.

For monorepos, separate root tooling from package commands. A root command may
not cover a workspace, and a workspace override may intentionally narrow policy.
Reconcile meaningful packages/subsystems with proposed guidance, without turning
the instruction file into a directory tour. Prefer tracked-file lists and focused
reads; dependencies, caches, and generated output do not need bulk inspection.

A useful command record has an actual command, working directory, prerequisites,
scope, expected result, and non-obvious caveats. Read scripts and config before
copying commands from prose. Do not install dependencies, launch services, run
migrations, or deploy anything to discover instructions. Static inspection proves
what a command is configured to do, not that it succeeded in this environment.

## Retention and Change Rubric

For each important existing rule, choose **retain**, **clarify**, **correct with
evidence**, **propose removal**, or **unresolved**. Preserve its useful section and
meaning. Never remove a domain constraint solely because its rationale is not
immediately apparent. Unsupported new guidance is omitted, not filled with a
placeholder section. A short instruction file may be complete; a long one may
contain necessary scoped detail. No fixed line count determines quality.

| Dimension | Practical question |
|---|---|
| Behavioral effect | Which plausible repository-specific error does this prevent? |
| Specificity | Does the rule point to actual interfaces, commands, or boundaries? |
| Operational clarity | Is the trigger/action understandable, including a relevant exception? |
| Conflict handling | Do applicable rules disagree for the same action/scope? Is this policy or implementation drift? |
| Noise and placement | Does the text add needed context, or duplicate another authority without a reason? |
| Relevant failure handling | Does it address demonstrated local failure modes rather than a generic checklist? |
| Observability | Could adherence be checked in actions, output, or the resulting diff? |

Use these dimensions as editorial prompts, not required sections or a performance
score. Optional requested 0–3 ratings mean weak/partial/functional/strong editorial
support only; they cannot measure model reliability or authorize deletion.
Qualifiers such as “prefer” are legitimate when the rule really is a preference.

Exercise a concrete deletion counterexample and a real collision scenario before
calling content dead or conflicting. A linter may enforce formatting yet still
need one instruction explaining the unusual wrapper used to invoke it. Conversely,
absence of a generic warning does not justify adding one to every repository.

## Edit and Readback Contract

A review returns findings in chat by default; no report file, scoring registry,
readiness grade, CI change, or document pack. Initialization creates only the
requested host/scope file when creation is authorized. Existing instruction edits
must be requested, not implied by an editorial score or a request to inspect.
Use a minimal patch, preserve unrelated content, read back the result, and inspect
the diff for semantic loss, duplicate imports/rules, wrong scope, and invented
commands. Keep uncertain operational claims out of new rules; explain important
unknowns in the response. Never claim that writing a file proved host loading or
that prompt text is executable enforcement.

Example acceptance cases: AGENTS-only repository needs no automatic Claude bridge;
coexisting Claude/AGENTS files require host-specific loading diagnosis rather
than merging them blindly; nested instruction conflicts require the actual
working directory and scope, not a global scoring rule.
