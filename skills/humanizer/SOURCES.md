# Sources and design choices

## External sources read for this version (2026-11-05)

| Source                                                                                                  | Used for                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Wikipedia, "Signs of AI writing": https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing           | Pattern catalog, vocabulary by model era (incl. the mid-2026 list), corrective disclaimers, em dash history, ineffective indicators, detector caveats |
| Agent Skills specification: https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx | Frontmatter limits (name 64, description 1024 chars), folder layout, under-500-lines recommendation                                                   |
| Claude Code skills docs: https://code.claude.com/docs/en/skills.md                                      | Description is truncated at 1,536 chars in the listing, put the key use case first                                                                    |

The Wikipedia page was read in full (raw text), not as a summary. It describes
encyclopedia edits; its examples were adapted to workplace documents here, and those
adaptations are design choices.

## User-supplied material

- The earlier `humanizer` skill (preservation contract, Detect/Rewrite/Edit modes, closed
  finding vocabulary, non-native register rules, em dash and idiom rules).
- The GPT-prepared v2 (`humanizer-v2.zip`): communication-situation check, genre table,
  speech-act and role rules, feedback handling. `references/context-cases.md` is taken
  from it with a new header.
- The research archive (`context-aware-humanizer-repaired-2026-11-05.zip`): research
  report, `context-aware-writer` skill, speaker-recipient fit, voice rules, the four
  failure signals from the meeting-notes incident (auditor questions, timeboxed agenda,
  assigned owners, ceremonial header). The 25 upstream skills it lists were not bundled
  in the archive and were not fetched for this version.

## Design choices (not from a measured study)

- Default-remove surface tells instead of judging them case by case. The earlier versions
  explicitly treated em dashes, bold, lists, and AI vocabulary as neutral; readers detect
  AI text by those features.
- Deterministic scanner plus token check, because self-review by the generating model does
  not see its own defaults. The scanner is advisory: its `suggestion` line never forces a
  rebuild, and accepted exceptions (`--allow`, `--allow-category`, plus a built-in list of
  technical terms such as "primary key") stop counting.
- Rebuild from a fact sheet when the role, genre, argument order, or structure is wrong;
  patch local tells; leave accepted or already direct text alone, whoever wrote it. This
  is v2's rule; v3.0.0 had widened it to "any model-written source" and 3.1.0 reverts that.
- Severity by consequence (v2's scale, restored in 3.1.0): meaning, role, commitment, and
  limitation changes outrank any number of style hits.
- Drafting in the user's name came from v2 (Draft mode and its description); the
  installed pre-v2 skill only covered requests to humanize.
- Russian and Ukrainian pattern lists, corporate idiom list, setup-reveal and staccato
  checks, and all scanner thresholds (CV < 0.35, mean < 11 words, 25% of sentences with
  three-item lists, the structural-category and density rules for the rebuild suggestion,
  the vocabulary cluster thresholds) are tuned on a handful of samples, not validated on a
  corpus.

## Known limits

- The scanner finds surface patterns. A clean scan does not mean the text sounds like the
  author; step 5 of the workflow and the user's own samples cover that.
- The token check compares presence of exact tokens (numbers, dates, identifiers, code
  spans, URLs) in both directions and reports a change in the number of negations. It
  does not count repeats (if "9" appears twice in the source and once in the draft, it
  reports nothing), does not read numbers written as words, and cannot tell that a claim
  was reversed or a limitation dropped. That is what step 5 of the workflow is for.
- AI style shifts with each model generation ([WP] documents at least four eras since
  2023). The vocabulary lists need updating as new models ship.

## 3.1.1 editorial additions (2026-11-09)

Five narrowly scoped rules were retained from the repository's previous
`skills/humanizer/SKILL.md`: neutral decision framing, current-behavior-first
durable documentation, strict brevity when requested, condition-first answers, and
flagging suspected factual errors instead of silently correcting them. The 3.1.0
scanner, patch/rebuild logic, role checks, and default AI-pattern removal remain
unchanged. These are editorial safeguards, not empirically validated improvements.
