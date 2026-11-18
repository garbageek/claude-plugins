# Technical and scientific writing

Improve the explanation while preserving its specification, evidence, and claim
strength. Use this reference for documentation, engineering reports, scientific
papers, research summaries, and other evidence-heavy prose.

## Contents

- [Content model](#preserve-the-content-model)
- [Engineering prose](#engineering-prose)
- [Scientific and research prose](#scientific-and-research-prose)
- [Mechanical checks](#mechanical-preservation-checks)
- [Limits](#limits)

## Preserve the content model

| Dimension | Preserve |
|---|---|
| Quantities | Values, signs, units, denominators, precision, ranges, intervals, thresholds, dates, versions |
| Scope | Dataset, population, environment, period, sample size, conditions, exclusions |
| Evidence status | Observation, estimate, hypothesis, interpretation, speculation, uncertainty, negative result |
| Causal strength | Association versus causation; necessity versus sufficiency; contribution versus guarantee |
| Operations | Actor, prerequisites, ordering, defaults, errors, compatibility, side effects |
| Exact syntax | Defined terms, identifiers, names, paths, commands, code, configuration, formulas |
| Attribution | Speaker, quotation boundaries, citation anchors, bibliography entries, full links |
| Work status | Proposed, implemented, tested, deployed, approved, completed, or unknown |

Protect relationships as well as tokens. “A outperformed B” and “B outperformed A”
contain the same names but opposite findings. An unchanged citation attached to a
different claim is still an error.

Style editing does not authorize rounding, unit conversion, formula repair, code
changes, version updates, or path normalization. Preserve a suspected factual error
and flag it separately; correct it only with authorization and supporting evidence.

## Engineering prose

Use one stable term per established referent. A worker, consumer, service, and process
may be different entities; consolidate labels only when the source establishes
identity. Keep terms such as “robust estimator” and “primary key” exact. A simpler
synonym can be wrong.

Keep ordered procedures, parameter tables, schemas, warning labels, accessibility
headings, and parallel reference entries structured. Their consistency supports
retrieval and correctness; do not vary definitions or command syntax for rhythm.

For durable reference documentation, describe current behavior in the documented
version. Preserve meaningful version boundaries. “We added the `mode` parameter”
can become a current-state entry only when the version and requested scope authorize
omitting that history. Release notes, changelogs, migration guides, and pull requests
usually need change narration.

Replace empty promotional framing with behavior already supplied. A claim that a
feature is fast or reliable remains a substantive claim even without a benchmark;
flag missing conditions instead of inventing a measurement or quietly deleting it.

Preserve a developer article's mechanism, trade-offs, and limitations. Do not insert
new code examples or claim compilation, execution, testing, deployment, or review
merely because the prose or syntax looks plausible.

## Scientific and research prose

Preserve “may,” “consistent with,” “in this sample,” “approximately,” confidence
intervals, and other evidence boundaries. Removing a hedge can change the result.
“No evidence of an effect” does not establish “evidence of no effect”; a nonsignificant
comparison does not establish equivalence. An association does not establish causation.
Flag conflicting findings; do not silently reconcile them.

Methods can center the procedure or sample. Keep a suitable passive; name an actor
only when the source supplies one. Preserve definitions, variable names, subscripts,
mathematical punctuation, statistical terms, and operation order. A statistical use
of “significant” is not promotional language.

Across a report, check that:

1. Question, contribution, abstract, results, and conclusion describe the same evidence
   at the same strength. A novelty claim needs support, not invented prior-art coverage.
2. Baselines, conditions, denominators, and comparison directions remain attached to
   the correct results. Do not fill missing experiments, mechanisms, or measurements.
3. Each paragraph advances the argument, reports evidence, states a limitation, or
   provides necessary context. Abstracts and reader-specific summaries may repeat findings.
4. Captions and cross-references match material actually available. Do not claim to
   inspect a figure when only its caption was supplied.
5. Compression preserves distinct claims and limitations. No fixed percentage reduction,
   sentence-length ceiling, or mandatory takeaway sentence applies.

Keep source assertions distinct from the editor's assessment. A bibliography can be
the requested evidence inventory; a missing citation is an attribution gap, not proof
of fabrication. Compilation, bibliographic validation, and data or figure checks are
separate tool-backed tasks. Report only checks actually performed.

## Mechanical preservation checks

Both helpers require Python 3.10+, use the standard library, and read **UTF-8 text or
Markdown** without modifying it. Resolve paths from the actual installed skill folder.

`ai_tells.py --source` runs the style scan and the count-aware preservation check:

```bash
python3 scripts/ai_tells.py edited.md --source original.md --json
python3 scripts/ai_tells.py edited.md --source original.md --allow-lines 8:14 --protect 'Exact Product Name' --json
```

Use the standalone checker when only preservation or a unified diff is needed:

```bash
python3 scripts/preservation_check.py original.md edited.md --json
python3 scripts/preservation_check.py original.md edited.md --allow-lines 8:14 --allow-lines 30:34 --protect 'Exact Product Name' --diff
```

`--allow-lines` uses inclusive **original-file** lines. Replacements and deletions
must stay inside them. An insertion requires both adjacent original lines to be
permitted, or the one existing boundary line at the start/end. Omitting the option
disables the scope check. `--protect` adds an exact source literal whose occurrence
count must remain. Both options require `--source` when using `ai_tells.py`.

The preservation check compares occurrence counts for recognized fenced code,
inline code, explicit blockquote lines, initial YAML frontmatter, common quotation
forms, URLs, citations, LaTeX/dollar math, numeric tokens, dates, selected identifiers
and paths, and explicit literals. It also checks line-ending styles and the UTF-8 BOM.
Repeated-value loss can therefore be flagged even when one copy remains.

The scanner retains its older presence-only `tokens_missing`/`tokens_added` output
and negation count as supplementary signals; the `preservation` JSON object contains
the stronger count and scope findings. `--allow` and `--allow-category` suppress style
candidates only; they do not suppress preservation findings.

Review every difference against the authorized edit. A new number may come from
supplied notes, and a removal may be explicitly requested. Keep an explanation for
an accepted difference; do not restore or hide it mechanically. A line number is a
locator, not a confidence score.

| Command | Exit behavior |
|---|---|
| `preservation_check.py` | 0: no mechanical issue flagged; 1: review differences; 2: input/execution error |
| `ai_tells.py` without `--fail-on` | 0: completed advisory report, even with findings; 2: input/execution error |
| `ai_tells.py --fail-on high` or `medium` | 1: a style candidate reaches the threshold, or a preservation/token/negation difference needs review; 0: no configured trigger; 2: error |

A nonzero review result is not proof of a bad edit or AI authorship. A clean result
is not proof of semantic equivalence. An error or skipped check is not a pass.

## Limits

These are conservative recognizers, not complete Markdown, citation, mathematics,
or language parsers. URL candidates retain terminal punctuation because it may
belong to the path or query; punctuation-only edits beside links can need review.
Not all proper nouns, units, reference styles, implicit blockquotes, indented code,
or machine-readable structures are recognized. Protect unrecognized exact phrases
explicitly and inspect structured content with its native document tool.

Numeric recognition preserves literal forms, including decimal punctuation, but
does not reliably interpret number words or associations between values and claims.
Moving a citation or swapping results between groups can evade count comparison.
Negation counts cannot identify which assertion was negated. A line diff can be
conservative or ambiguous in repetitive files. Always inspect the source/result
pair and actual diff.

Inputs containing NUL, invalid UTF-8, invalid line ranges, or more than 8 MiB per file
are rejected. Use format-native tools for binary documents. Neither helper verifies
factual truth, preserves meaning by itself, or measures a match to the author's voice.
