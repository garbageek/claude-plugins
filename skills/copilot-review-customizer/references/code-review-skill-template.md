# Generated code-review skill: section roles

This file defines what each section of a generated `.github/skills/code-review/SKILL.md` is for. When a different mechanism is chosen, the same section roles and both gates apply to that file; drop the skill frontmatter. It is not content to copy and not a mandatory layout. Skill selection depends on the name and description, so a precise description and high-signal body matter more than structure. Omit any section the repository gives no evidence for; an empty section is worse than no section. Keep the two gates in meaning even if you restructure. Replace every `<placeholder>`.

## Size and shape

- Aim for one screen per section and well under the ~1,000-line guidance for instruction files; most repositories need far less.
- Move long per-domain detail into sibling files in `.github/skills/code-review/` (for example `persistence.md`) and reference them by relative path.
- Reference repository files by path. Rules stay self-contained; an external URL may appear only as provenance, never as the place the rule lives.
- Imperative bullets, one rule per bullet, each repository-specific rule traceable to ledger rows.
- Steady-state wording only: no "after cutover", "for now", "during the migration". State invariants, not the remedy one fix happened to use.

## Skeleton

```markdown
---
name: code-review
description: PR and code review guidance for <repository name>. Use when reviewing pull requests in this repository, especially changes to <domain 1>, <domain 2>, <domain 3>. Covers project contracts, known regressions, intentional patterns, and what counts as a defect here.
---

# Code review: <repository name>

## Scope
<!-- One or two lines: what this repository is and which areas of the diff this guidance targets. -->

## Finding gate
Optimize for precision: no finding is better than an unsupported one, but report every defect you can prove.
A defect claim, at any severity, needs every link:
`activation -> changed hunk -> reachable scenario -> failure mechanism -> observable impact -> evidence`
- Name the changed file and hunk, the scenario that reaches it, the concrete mechanism, the observable impact, and the repository file, normative document, or code semantics that establish it.
- A repository rule the diff cannot violate produces no finding.
- Static proof is enough: call paths, types, guards, control flow, language semantics. No runtime run, past incident, or written rule is required.
- Before reporting, check callers, guards, fallbacks, and handlers that could refute the defect.
- Low severity does not excuse a missing link.
- Not defects by themselves: missing tests, PR size, production exposure, shared state, complexity, inability to run code or UI, and theoretical risk without a demonstrated call path.
- Unchanged code is out of scope unless the diff changes its inputs, reachability, or contract.
- A review with no findings is a valid result.

## Sources of truth
<!-- Only files that genuinely define behavior. One line each: path, what it defines, when to consult it.
Example shape: `schemas/<x>.json`: wire format for <y>; check changes to serializers against it. -->

## Contracts
<!-- Only accepted ledger rows. Each bullet: activation (which paths or changes), contract (behavior, not implementation detail), where to verify, known-bad mechanism, evidence path.
Wording strength matches evidence strength. -->

## Known regressions
<!-- Only mechanisms that pass the historical regression test. Shape: when a change does X, verify Y still preserves Z; regression <PR or commit> occurred when mechanism M bypassed it. -->

## Intentional patterns (not defects here)
<!-- Patterns a generic reviewer tends to flag that this repository uses on purpose. Each bullet: pattern, why it is intentional, evidence path. -->

## Manual verification (not defects)
Add a manual-verification item only when the diff creates a specific question that materially affects changed behavior and repository evidence cannot settle statically. State the exact action, the condition, and the expected result. Never add broad items such as "test this manually" or "verify the UI"; if the basis is missing, add nothing.
<!-- Optional: list known repository areas where this typically applies, each with the exact check and expected result. -->
```

## Section guidance

| Section              | Include when                                                                    | Typical failure to avoid                                       |
| -------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Scope                | Always                                                                          | Restating README                                               |
| Finding gate         | Always; wording may be adapted, meaning may not                                 | Adding comment-format rules (unsupported)                      |
| Sources of truth     | Files exist that define behavior more precisely than code review can infer      | Listing every config file                                      |
| Contracts            | Accepted ledger rows exist                                                      | Freezing a replaceable implementation choice                   |
| Known regressions    | History confirms a mechanism                                                    | Vague rules ("watch performance", "check migrations")          |
| Intentional patterns | History or code shows a generic reviewer misreading a deliberate pattern        | Unevidenced exemptions that hide real defects                  |
| Manual verification  | Specific diff-induced questions need runtime, UI, environment, or external data | Broad "test manually" items, or phrasing that implies a defect |

## PR description skeleton

```markdown
## Why
<!-- Observed problem: speculative findings, missed regressions, generic advice. Cite review history if any. -->

## What this adds
<!-- Files added or changed and the mechanism decision. Why rejected mechanisms were not needed. -->

## Contracts encoded
<!-- One line per contract with its evidence path. -->

## Regressions covered
<!-- One line per historical check with its fix reference, or "none confirmed". -->

## False-positive classes targeted
<!-- Classes from the review-history analysis, with example PRs. -->

## How to evaluate
<!-- Status, kept separate: files prepared / loading confirmed by docs / use observed (attributions or session log) or "use not confirmed" / benefit confirmed (not yet).
Dogfood: Copilot review on this PR; confirm attributions reference the skill (Markdown-only diff does not exercise contracts).
Next reviews: compare finding precision by class (confirmed vs speculative, coverage-only, generic, broad manual checks) against the baseline above.
Optional replay: throwaway draft PRs reapplying historical bug diffs, closed unmerged. -->

## Maintainer note
Copilot reads review guidance from the PR head branch, so changes to `.github/skills/**`, `.github/instructions/**`, and agent instruction files deserve the same review as code.
```
