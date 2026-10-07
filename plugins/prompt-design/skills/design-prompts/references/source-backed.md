# Source-backed prompt mode

Use through [design-prompts](../SKILL.md) when the user asks for agent instructions derived from implemented service/workflow behavior. The result is a usable prompt, not registration code, a new agent framework, or execution of the service.

## Discover the actual contract

Read the supplied source and relevant project requirements. Identify real entry points, input/output models, validation rules, routing, state transitions, exported results, and callers. Do not assume a particular stage registry, class name, private development standard, or companion skill. An inaccessible source stays unavailable; do not infer its behavior from a filename.

Trace the selected workflow in order. Include applicable failure/partial/no-op outcomes, constraints, independent-role requirements, and side effects. Distinguish the implemented executable branch from comments describing an aspiration. Read existing prompt templates as one source, not as proof that a deterministic gate exists.

## Map behavior to instructions

For each retained rule identify:

| Source evidence | Implemented behavior | Prompt instruction | Enforcement owner / required tool | Gap or assumption |
|---|---|---|---|---|

Use actual repository-relative file/function/line or revision references. Map terminology only when the target contract supports the equivalence; preserve exact IDs, enums, field semantics, ordering, and required inputs. A similarly named stage is not necessarily the same operation.

Keep only behavior within the requested source scope. Separate unsupported, unreachable, ambiguous, or environment-dependent behavior rather than inventing a complete workflow. If source and target contracts disagree, state the difference and which mapping cannot be promised.

## Preserve executable enforcement

A programmatic validation, authorization check, transaction, retry limit, or state-transition gate remains executable code. Describing it in natural language does not preserve its enforcement. In the prompt, identify when to call the actual tool, its required inputs and observed success/failure outcomes, and what the surrounding controller still enforces.

Use only tools and input/output capabilities actually available to the target agent. Missing runtime support is an explicit dependency or limitation, not a fabricated callable. A rules-based service and a model-backed implementation need not have equivalent guarantees. Do not translate code into an instruction that claims identical determinism, validity, or side effects.

## Deliver

Return one self-contained prompt using the main skill's output contract. Normally include a compact source-to-instruction mapping and unsupported-behavior notes outside it so the derivation is reviewable. For prompt-only output, omit outside commentary; preserve required runtime dependencies and uncertainty handling inside the prompt. Do not add a separate traceability file or expose implementation-only details to the target when they are not needed.

A useful prompt shape is:

````text
# <Workflow purpose>

## Objective
<Source-backed outcome>

## Inputs
<Actual target inputs and missing-input behavior>

## Procedure
<Observed stage decisions mapped to supported agent actions>

## Output
```json
{"illustrative_field": "Replace with the actual target output contract"}
```

## Constraints and failures
<Executable gates/tool dependencies, unsupported outcomes, stop boundary>
````

Replace illustrative fields before delivery; this is a shape, not a source fact. Validate fence nesting, defined placeholders, coverage of the requested source behavior, actual target-tool names, and the boundary between prompt guidance and code enforcement. Do not register a stage or edit service code unless separately authorized.
