---
name: review
description: Review scoped repository instructions against actual code, commands, and Claude/Codex loading behavior. Identify drift, conflicts, noise, and useful retained rules; return source-backed minimal changes without editing unless explicitly requested.
---

# Review Repository Instructions

Read [discovery and retention](../../references/discovery-and-retention.md). Review
is **read-only by default**, including no report file creation. It does not run
services or modify host settings merely to verify a documentation claim.

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

When the request includes applying improvements, edit only the named scope and
preserve useful content/organization. No automatic deletion, import-chain
rewrite, policy hierarchy invention, or new instruction-file family. Read back
the result and compare against both source evidence and the original meaning.
An edit does not prove the host loaded it; record any unverified loading behavior
without claiming success. For missing-file creation, use [init](../init/SKILL.md).

For repository-specific **GitHub Copilot Code Review customization**, use
[copilot-review-customizer](../copilot-review-customizer/SKILL.md). That workflow
selects Copilot's review surfaces and uses review/regression history; it does not
change this skill's Claude/Codex initialization or instruction-review contract.
