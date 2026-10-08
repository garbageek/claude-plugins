# Operator surfaces

Use when a displayed label, setting, log, export, or request appears to disagree with the effective behavior. Start with one concrete operator question, then inspect actual artifacts. Apply the [deep-review finding contract](../SKILL.md).

## Map independent dimensions

A surface can be both authoritative and an input. Do not put it into one mutually exclusive bucket.

| Dimension | Questions |
|---|---|
| Authority | Which value controls this particular decision? Is this canonical state, a derived snapshot, an override, or unknown? |
| Transformation | What filtering, expansion, templating, normalization, truncation, serialization, or defaulting produced this representation? |
| Visibility | Is the full value observable, partially rendered, summarized, captured at a boundary, or unavailable? |
| Consumer | Human operator, application code, log reader, model/API client, provider, or another component? |

For each relevant surface record its actual name, location, producer, consumer, time/revision/request identity, the four dimensions, and supporting evidence. Follow the transformation chain from configured value to effective value and onward to the observable consumer boundary. A display label and a stored identifier can both be valid without being interchangeable.

## Questions that expose meaningful divergence

- Does a command/flag change only rendering, or also semantics, filtering, freshness, or scope?
- Is a debug summary being presented as the complete request? Which omitted fields matter?
- Do original, expanded, optimized, persisted, and displayed values refer to the same request/version?
- Does an alias obscure a different command or merely provide a second spelling?
- Does a visible control show the value actually submitted, or current form state unrelated to the saved job?
- Does an export reflect canonical state, or reconstruct it with a fallback parser?

Inspect the actual implementation and captured artifacts before asserting drift. A representation difference is a defect only when it violates the relevant contract or misleads its consumer; otherwise explain the deliberate transformation.

## Observable boundary

A captured outbound request establishes what that client submitted at that boundary. It does **not** prove what a remote provider later transformed, retained, or supplied internally to a model. Use “captured outbound fields” rather than “exactly what the model saw” unless that stronger claim is directly observable and supported. Do not infer hidden context from token counts, logs, summaries, or a nearby payload.

When a canonical value is inaccessible or split across artifacts, say what is known, which surface is missing, and what observation would settle the question. Do not substitute the closest diagnostic view for the unavailable truth.

Return a compact surface map and evidence-backed differences. Preserve actual names/IDs; propose a minimal rename, alignment, or exposure only when relevant, and do not apply changes on review authority alone. No new truth registry, diagnostics runtime, or cleanup artifact is required.
