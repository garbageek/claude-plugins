# Existing test-quality analysis

Assess existing tests against the behavior they claim to protect. This reference does not authorize running, generating, editing, or deleting tests. Use one consolidated [deep-review result](../SKILL.md), not per-file reports or an index.

## Trace protection, not activity

For each relevant contract, follow **contract → scenario/setup → real subject execution → assertion → failure consequence**. Identify which behavior is real and which boundary is substituted. Ask: **what plausible change to production behavior would make this test fail?** Reason about that change; do not introduce mutations without authorization.

An assertion that cannot distinguish the relevant correct and incorrect behavior is a gap. Just executing the path is not sufficient. Conversely, “does not raise,” “not None,” a status code, call ordering, or a mock interaction can be exactly the intended contract. Judge their scope before declaring them useless. A mock returning the asserted value may still exercise meaningful transformation, dispatch, or validation; inspect the real subject path.

## Canonical review checklist

| Dimension | Inspect and record |
|---|---|
| Reachable assertions | Empty bodies, swallowed exceptions, skipped assertions, conditional paths that never check a result |
| Can it fail? | A realistic behavior change the assertion rejects; wrong/partial/empty output it still accepts |
| Intent and contract | Named scenario and expected result, real product/system relevance, distinct protection versus duplication |
| Behavior versus implementation | Observable output/state/side effect; whether harmless refactoring breaks the test; whether a copied algorithm replaces independent expectations |
| Assertion strength | Meaningful values/errors/content; ordering only when contractual; snapshots with an understood purpose; useful failure diagnostics |
| Domain data | Values exercising the actual boundary; minimal realistic fixtures; irrelevant filler and oversized setup distinguished from necessary integration data |
| Boundaries and failures | Applicable empty/invalid/min/max input, rollback, timeout, retry exhaustion, partial failure, and the reported regression |
| Substitution boundaries | Real subject logic runs; mocks/fakes match the external contract; interaction assertions protect a real interface |
| Determinism and isolation | Clock/random/order/shared-state dependencies; actual isolation of external state; synchronization instead of guessed waiting |
| Structure | Understandable setup/action/assertion; helpers do not conceal the tested behavior; parameterization preserves distinct cases |
| Test level | What unit, integration, contract, or end-to-end evidence actually covers; no claim that a mocked boundary proves the deployed integration |
| Coverage versus confidence | Which failures are rejected rather than how many lines execute; uncovered paths are unknown, not automatically broken |
| Maintenance and execution context | Flaky/slow/setup-dependent behavior supported by actual evidence; existing CI context and limitations, not guessed results |

Missing coverage is an assessment of protection, not proof of a production bug. A known-regression test is strong evidence only when it exercises the failure condition and checks its consequence. Do not label an unrun test passing or deterministic.

## Decisions and optional rubric

Recommend **keep**, **strengthen**, **rewrite**, or **delete** only with the contract and concrete reasoning. Deletion is a proposal, never a consequence automatically applied by a score. Distinguish duplicate protection from an independent integration boundary.

Where useful, annotate dimensions as adequate / weak / unsupported / not applicable. Any numeric values explicitly requested by the user are reviewer heuristics, not measured correctness, measured coverage, or model performance. Do not let an aggregate score hide a missing central assertion; do not use hard thresholds based on file length, number of assertions, or the mere presence of a pattern.

The consolidated result identifies protected contracts, representative assertions, realistic failures caught versus missed, contextual recommendations, and unobserved execution limits. Map confirmed audit findings to the existing contract only if ticketization is requested. Do not manufacture a testing project from a review request.
