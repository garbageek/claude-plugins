---
name: review-repo-instructions
description: Review an existing agent instruction file (AGENTS.md, CLAUDE.md, .claude/rules) against the actual code, commands, and Claude/Codex loading behavior. Use when asked to check, audit, or review such a file, or to find out why an agent does not follow it. Reports drift, conflicts, noise, and rules worth keeping, with minimal source-backed changes; edits only when the request or standing project instructions authorize it. For a requested rewrite, or a new rule after an agent failure, use design-prompts.
---

# Review Repository Instructions

Read and apply [the delivery contract](../../references/delivery-contract.md) within this skill's scope and authorization.

Read [discovery and retention](../../references/repo-instructions.md). Review
is **read-only by default**, including no report file creation. It does not run
services or modify host settings merely to verify a documentation claim.

The read-only default yields to the request and to the project's or user's standing instructions. If
either says that a check includes fixing confirmed problems, finish the review,
then apply the corrections for **confirmed drift/conflict** under Authorized Edits
in the same turn. Editorial suggestions and unresolved behavior stay proposals.

## Investigation

Read the complete target and the actual applicable instruction chain. Inspect
referenced scripts/configuration and representative consumers before deciding a
rule is stale. Verify the working directory and host loading scope, especially
when Claude/AGENTS files coexist or nested overrides disagree. If loading cannot
be observed, distinguish documented expected loading from observed loading.

Apply the shared seven-dimensional editorial rubric. Use real deletion and
collision scenarios, not random line sampling or fixed length thresholds.
Distinguish an obsolete fact from an intended constraint the implementation is
violating. Retain important rules whose rationale needs clarification rather
than silently deleting them. Never add a generic warning or policy just to raise
a score, and never use a low score to justify rewriting a whole file.

## Finding Shape

For each material finding, state the existing rule and location, applicable
host/scope, observed repository evidence, concrete consequence, proposed smallest
change, and remaining uncertainty. Separate **confirmed drift/conflict**,
**editorial suggestion**, and **unresolved behavior**. Include valuable content to
retain when a proposed edit could otherwise lose it. Return one consolidated
result, not per-file reports or a grading dashboard. Use optional numeric rubric
ratings only when requested, explicitly as editorial judgment, not measured
model effectiveness.

## Authorized Edits

When edits are authorized, edit only the named scope and
preserve useful content/organization. No automatic deletion, import-chain
rewrite, policy hierarchy invention, or new instruction-file family. Read back
the result and compare against both source evidence and the original meaning.
An edit does not prove the host loaded it; record any unverified loading behavior
without claiming success. For missing-file creation, use [init](../init-repo-instructions/SKILL.md).
When the user explicitly asks to rewrite, compress, or restructure an instruction
file, or to add a rule after an agent failure, use the standing-instructions mode
of [design-prompts](../design-prompts/SKILL.md).

For repository-specific **GitHub Copilot Code Review customization**, use
[copilot-review-customizer](../copilot-review-customizer/SKILL.md). That workflow
selects Copilot's review surfaces and uses review/regression history; it does not
change this skill's Claude/Codex initialization or instruction-review contract.
