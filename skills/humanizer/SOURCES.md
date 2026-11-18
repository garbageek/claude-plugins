# Sources and design choices

## Current baseline: Humanizer 3.2.0

This revision combines the two user-supplied implementations. The current workflow
is defined by `SKILL.md` and its references; historical design choices below are
provenance, not instructions to apply an older default.

| Supplied source | Retained strengths | Reconciled behavior |
|---|---|---|
| Artur Plugins Humanizer 3.1.2, in `claude-plugins-main (5).zip` | Drafting in the user's name, workplace role/genre checks, patch versus rebuild, accepted-feedback handling, EN/RU/UK scanner, practical examples, existing interface/assets | Pattern matches are candidates; blanket word/format bans and zero-hit stopping rules are removed. |
| `humanizer-production.zip` (no version declared in its frontmatter) | Context gates, preservation of unsupported substantive claims, evidence-based voice calibration, technical/scientific constraints, count-aware preservation and original-line scope checks | Added the drafting route and existing scanner rather than replacing them; integrated the checker into `ai_tells.py --source`. |

Production's large catalog is consolidated into `references/patterns.md`, not copied
as a second competing catalog. Voice calibration is integrated into the existing
`references/voice-profile.md`. Context routing and technical details have separate,
conditionally loaded references.

## Current design choices

These are editorial and implementation choices, not measured accuracy claims.

- Require a demonstrated defect and a safe correction. A dash, triad, passive,
  uncertainty phrase, repeated technical term, or heading is not an error by itself.
  Explicit author preferences still govern the requested voice.
- Keep unsupported substantive assertions and flag evidence gaps separately.
  Removing empty framing must not erase a claim, qualifier, comparison, or criticism.
- Retain the independent scanner as a source of review candidates. Its severity is
  heuristic strength, separate from consequence-based editorial severity.
  Its suggestions never require a rewrite or rebuild.
- Retain local patches for local problems and section rebuilding for a demonstrated
  role, artifact, or organizational failure. Preserve accepted edits.
- Use source content for facts and comparable author samples for style. Distinguish
  observed, requested, tentative, and unsupported voice traits; do not infer a
  biography or transfer sample facts into the target.
- Run the stronger preservation comparison automatically with `--source`.
  It counts recognized occurrences, protects blocks and exact literals, and can
  check original-line boundaries. Existing token summary keys remain available;
  they do not replace the detailed `preservation` result.
- Keep `--allow` and `--allow-category` confined to style candidates. Neither can
  hide protected-content changes. `--allow-lines` permits locations, not semantic
  changes or invariant loss.
- Preserve read-only helpers with standard-library dependencies. Python 3.10+ is
  needed for the helpers; the manual editorial workflow does not require Python.

## Historical external-source provenance

The 3.1.2 source records the following material as read on 2026-11-05.
Those source-reading claims belong to that revision; the merge does not claim a new
external review or use these pages as empirical validation of scanner thresholds.

| Recorded source | Role in the earlier version |
|---|---|
| [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) | Vocabulary and surface-pattern examples, ineffective indicators, detector caveats. Encyclopedia-editing examples were adapted to workplace prose. |
| [Agent Skills specification](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx) | Frontmatter and package-layout guidance. |
| [Claude Code skills documentation](https://code.claude.com/docs/en/skills.md) | Earlier host-discovery and description guidance. |

Wikipedia pattern examples are not a validated classifier for workplace, scientific,
personal, or multilingual writing. `[WP]` notes in the inherited scanner mark
provenance, not proof that a given match is wrong. `[M]` refers to supplied materials;
`[D]` marks a design choice. Historic model-era vocabulary labels do not establish
when or by whom a passage was written.

## Earlier supplied material

The 3.1.2 provenance records:

- An earlier Humanizer with preservation, Detect/Rewrite/Edit modes, finding labels,
  and non-native-register rules.
- `humanizer-v2.zip`, which added communication context, genre routing, role and
  speech-act preservation, and feedback handling.
- `context-aware-humanizer-repaired-2026-11-05.zip`, containing a research report
  and context-aware writing instructions. The 25 upstream skills listed there were
  not bundled or fetched for 3.1.2.

The present merge directly inspected the two supplied archives listed at the top;
it does not claim independent inspection of these earlier artifacts.

## Known limits

- Pattern lists, vocabulary sets, rhythm thresholds, density rules, and repeated-hit
  escalation are heuristics inherited from a small set of examples, not a validated
  corpus. EN, RU, and UK do not have equal rule coverage. A clean scan establishes
  neither good writing, author resemblance, nor human authorship.
- The preservation helper is a conservative UTF-8/Markdown recognizer, not a parser
  for every document format. It may flag authorized edits and overlapping tokens.
  Unrecognized names, units, number words, syntax, or implicit structure need explicit
  protection or manual review. See the technical reference for exact coverage.
- Occurrence counts cannot track semantic relationships. Swapping subjects, attaching
  a citation to another claim, exchanging values between groups, or changing a modal
  verb can pass a mechanical comparison.
- Negation counts are an additional review cue, not a logical-equivalence check.
  An unchanged count can conceal a reversal; a changed count can be an authorized
  clarification.
- Original-line scope uses a line diff. Repeated text can produce ambiguous alignment;
  insertion boundaries are deliberately conservative. Inspect the actual saved diff.
- `--fail-on` is an opt-in gate for reported candidates/differences. Default scanner
  success does not mean there were no findings. A checker error is not a completed
  comparison. Host installation and model behavior require their own evidence.

## Retained revision history

**3.1.1 (2026-11-09):** Added neutral decision framing, current-behavior-first durable
documentation, requested brevity, condition-first answers, and separate factual-error
flagging. These remain subject to claim and version-scope preservation.

**3.1.2 (2026-11-09):** Preserved decimal commas in the old token normalization and
supported accepted phrases across soft line wraps. Examples used generic invented
systems and roles. The earlier default-removal policy is superseded by 3.2.0.

**3.2.0 (2026-11-18):** Combined context-sensitive editing with the existing drafting
and scanning workflow, integrated count-aware preservation, strengthened voice and
technical guidance, and reconciled worked examples with their stated source facts.
