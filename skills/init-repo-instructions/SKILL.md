---
name: init-repo-instructions
description: Create repository-specific agent instructions for the requested Claude or Codex scope from real commands, boundaries, and non-obvious constraints. Preserve existing guidance; use when initializing instructions, not transforming the whole repository.
---

# Initialize Repository Instructions

Read [discovery and retention](../../references/repo-instructions.md) before
choosing a target file. It owns the shared evidence rubric and host-specific
loading rules; do not invent a second precedence policy here.

1. Resolve the requested host/scope and existing instruction chain. Prefer the
   established file and actual loading mechanism. Do not automatically generate
   both `AGENTS.md` and `CLAUDE.md`, a bridge, local overrides, or nested files.
2. Read existing instructions, manifests, commands, workspace boundaries,
   generated/manual sources, and relevant implementation evidence. Identify
   mistakes an agent would otherwise make; omit generic advice and directory
   inventories. Use the repository's own project type and terminology.
3. Draft only supported, actionable rules: actual commands with necessary
   working-directory/prerequisite details, responsibilities, unusual conventions,
   generated-file handling, and verified recurring pitfalls. No invented service,
   branch, deployment, test-creation, or documentation policy.
4. If the requested file is missing and creation is explicitly authorized, create
   that one file. A request for a draft/proposal returns content without writes.
   If useful instructions already exist, do not replace or rearrange them to
   impose a preferred skeleton; propose the smallest update unless editing is
   already authorized. Do not re-ask permission for the exact approved edit.
5. Read back any authorized edit and inspect the diff. Preserve valuable original
   rules and headings, omit empty/unverified sections, and report the actual file
   changed. Describe loading as unverified unless the host really confirmed it.

Use [review](../review-repo-instructions/SKILL.md) when the task is primarily to assess an existing
file. No ancillary reports, inventories, configuration changes, ready-made file
matrix, hooks, or all-purpose “AI-ready” operation are part of initialization.

For repository-specific **GitHub Copilot Code Review customization**, use
[copilot-review-customizer](../copilot-review-customizer/SKILL.md). That workflow
selects Copilot's review surfaces and uses review/regression history; it does not
change this skill's Claude/Codex initialization or instruction-review contract.
