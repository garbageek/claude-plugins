# AI-writing tells: catalog and fixes

Category names match the scanner output (`scripts/ai_tells.py`). Source tags:

- **[WP]** Wikipedia, "Signs of AI writing" (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), read in full on 2026-11-05. It describes encyclopedia edits; the workplace examples below are adaptations.
- **[M]** The user's own research materials and earlier corrections (meeting-notes failure, role drift, non-native register).
- **[D]** Design choice of this skill, based on common corporate AI output. Not from an external study.

The goal in every case is the same: replace the pattern with the specific fact it was
standing in for. If there is no fact behind it, delete it.

## 1. Chatbot leakage and placeholders (HIGH) [WP]

Text addressed to the person who prompted the model, left in the document.

- "I hope this message finds you well", "Here's a revised version", "Below is a summary",
  "Let me know if you'd like me to...", "Feel free to reach out", "I hope this helps",
  "Great question", "Certainly!"
- Unfilled slots: `[Your Name]`, `[Insert date]`, `[link]`, `2026-XX-XX`, `INSERT_URL`.
- Tool residue: `utm_source=chatgpt.com` or `utm_source=openai` in links, `oaicite`,
  `contentReference`, the `↩` footnote marker.

Fix: delete. Strip `utm_source` parameters from URLs. Fill or remove every slot; never
deliver a placeholder.

## 2. Puffery: significance, legacy, importance (MEDIUM) [WP]

The model adds statements about how important something is instead of saying what it
does. Watch for: plays a crucial/key/vital/pivotal role, is a testament to, marks a
significant shift, a key milestone, setting the stage for, paving the way, underscores
the importance of, highlights the need for, reflects broader, evolving landscape,
valuable insights, "This matters", "Why it matters".

- Before: "Switching to incremental processing will play a crucial role in improving reliability."
- After: "With incremental processing, a late file no longer breaks the load. All 4 October failures
  were late files."

- Before: "This matters for two reasons."
- After: just give the two reasons.

## 3. Participle tails (MEDIUM) [WP]

A comma and an -ing clause appended to a factual sentence to comment on it: ", ensuring
...", ", highlighting ...", ", underscoring ...", ", reflecting ...", ", enabling ...",
", contributing to ...", ", positioning us to ...". Russian: ", что позволяет ...",
", обеспечивая ...", ", подчёркивая ...".

- Before: "The job failed 4 times in October, highlighting the need for a more robust
  approach."
- After: "The job failed 4 times in October."
  (If the need for a fix is the point, the next sentence proposes the fix.)

## 4. Copula avoidance (MEDIUM) [WP]

"serves as", "stands as", "functions as", "acts as", "boasts", "features", "represents"
where "is" or "has" is meant. Models measurably avoid "is" and "are"; AI copy-edits
replace them.

- Before: "This table serves as the single source of truth for revenue."
- After: "This table is the source of truth for revenue."

## 5. Negative parallelism and corrective framing (MEDIUM) [WP]

Correcting a misconception nobody voiced.

- "not just X, but Y", "not only X but also Y"
- "It's not X, it's Y", "This isn't about X; it's about Y", "less about X, more about Y"
- "Y rather than X" as a sentence rhythm (one real comparison is fine; two or more in a
  short text is a tell)
- Mid-2026 disclaimers: "does not (by itself) establish/guarantee/prove", "should be
  treated as ... rather than ...", "should not be confused with", "based on the available
  information", "not widely documented". [WP] dates these to models released from
  mid-2026, which makes them the freshest tell in current GPT output.
- Russian/Ukrainian: «не просто X, а Y», «это не X — это Y», «не только ..., но и ...»
  used as a flourish.

Fix the wording, never the claim. Both parts of the contrast usually carry meaning, and a
real limitation must keep its full strength.

- Before: "The issue is not just a scheduling problem; it's a fundamental gap in how we
  handle late-arriving data."
- After: "Part of it is scheduling, but the bigger problem is that the load has no way to
  handle files that arrive late."
  (The source says scheduling is part of the problem; "the scheduler is fine" would
  change that.)

- Before: "Late events were rare in October. The October test does not establish that
  late events are rare in general."
- After: "Late events were rare in October, but one month of data doesn't tell us whether
  they are rare in general."
  (Same limitation, plain wording. Dropping it, or turning it into "late events are
  rare", would change what is known.)

## 6. Setup-reveal and rhetorical Q&A (MEDIUM) [D]

"The result? ...", "The fix: ...", "Here's the thing", "Here's why", "The bottom line:",
"Why? Because ...". Copywriting rhythm; nobody writes a status update this way.

- Before: "The result? Fewer failures, fresher data, and happier stakeholders."
- After: "Dashboards would be current by 03:00 instead of after a manual rerun."

## 7. Signposting, purpose statements, wrap-ups (MEDIUM) [WP][M]

- Purpose statements: "This document outlines/provides/aims to...", "The purpose of this
  memo is...". Start with the point instead.
- Tour-guide phrasing: "Let's dive into", "Let's take a closer look", "Let's break it
  down", «давайте рассмотрим».
- Didactic asides: "It's worth noting that", "It is important to note", "Notably,",
  "Importantly,", «важно отметить», «стоит отметить», «варто зазначити».
- Wrap-ups: "Overall,", "In summary,", "In conclusion,", "Ultimately,", "Key
  takeaways", a final paragraph restating the document, «в целом», «таким образом»,
  «подводя итог».

Fix: delete the frame and keep what follows it, if anything. A long report can have a
short summary at the top if the reader needs one; never one at the bottom too.

## 8. Rule of three (MEDIUM) [WP]

Lists of exactly three adjectives or phrases used for rhythm: "scalable, resilient, and
efficient", "fewer failures, fresher data, and happier stakeholders", "the challenges,
proposed solutions, and next steps". Also sections that always contain three bullets.

Fix: keep the items that carry information, however many that is. Usually one.

## 9. AI vocabulary (MEDIUM, HIGH in clusters) [WP][D]

One or two of these can be coincidence. Several together is one of the strongest tells.
Rewrite the sentence with the concrete fact; don't swap in a synonym.

- Classic (2023 to 2025 models): delve, tapestry, testament, pivotal, crucial, vibrant,
  intricate, interplay, underscore, showcase, foster, garner, bolster, meticulous,
  seamless, holistic, synergy, realm, embark, harness, cutting-edge, ever-evolving,
  landscape, navigate (figurative), enhance, align with, highlighting, emphasizing.
- Mid-2026 models per [WP]: challenge, clearer, dependable, echoed, foster, leverage,
  matters, multifaceted, practical, prioritize, quietly, steady, universally.
- Corporate filler [D]: leverage, robust, streamline, utilize, facilitate, empower,
  elevate, actionable, impactful, scalable, proactive, stakeholders, comprehensive,
  ensure that, deep dive, circle back, touch base, move the needle, low-hanging fruit,
  north star, best-in-class, game-changer, going forward, moving forward.
- Russian/Ukrainian [D]: является, данный, в рамках, осуществлять, ключевой, комплексный,
  уникальный, широкий спектр, максимально, обеспечивает, позволяет, играет важную роль,
  в современном мире, на сегодняшний день; відіграє роль, здійснювати, даний, у рамках.

Plain replacements that are usually right: use, help, check, fix, show, need, start,
about, has, is, more, less, faster, cheaper, the actual number.

Literal meanings are fine: "underscore" as a character, "landscape" as page orientation,
"key" in "primary key".

## 10. Hedging (MEDIUM) [M]

Stacked qualifiers: "may potentially", "could possibly", "it seems that it might",
«может потенциально». One accurate qualifier is enough. Real uncertainty is said
concretely: "I measured only October."

## 11. Formatting tells [WP][M]

- **Bold lead-in bullets** ("- **Root cause:** late files"). The most recognizable
  layout of a model answer. Write sentences, or a plain list without labels.
- **Bold in running text.** Remove; if one thing must stand out, put it first.
- **Headings in a short text.** Under about 400 words, a status update or email needs no
  headings. Never "Purpose", "Executive summary", "Key findings", "Next steps" on a
  one-page note.
- **Title Case Headings.** Use sentence case.
- **Emoji** in headings or bullets. Remove.
- **Em dashes** in English. Many readers treat them as an AI signature. [WP] notes newer
  OpenAI models suppress them while Claude still uses them more than professional
  writers. Replace with a comma, colon, parentheses, or a period. In Russian and
  Ukrainian the dash is normal punctuation.
- **Punctuation monotony.** The overcorrection: only commas and periods for a whole page
  [WP]. Parentheses and a colon before a list are fine.
- **Horizontal rules** between sections of a short text. Remove.
- **Curly quotes** in Markdown or chat mixed with straight ones. In a Word document they
  come from autocorrect and are fine.

## 12. Rhythm (MEDIUM) [WP][D]

- **Uniform length.** Most sentences 12 to 18 words, all paragraphs three or four
  sentences. Scanner: CV of sentence length below 0.35.
- **Staccato.** The 2026 pattern: chains of 6 to 10 word declaratives, each starting
  with "This" or "It" ("This takes 40 minutes. It also uses a large warehouse. The cost is
  steady."). [WP] notes a strict 8 to 20 word band in mid-2026 output.
- **Repeated openers.** Several bullets or sentences starting the same way.

Fix: join sentences that are one thought ("The rebuild takes 40 minutes on an L
warehouse, which is most of our nightly credit spend."), and keep short sentences for the
things that deserve the stress. Don't insert random fragments.

## 13. Service and consultant register [WP][M]

- Customer-service lines: "Please don't hesitate to", "Thank you for your patience",
  "I wanted to reach out", "I trust this clarifies".
- Consultant/auditor voice from an insider: asking the manager who owns a table the
  author works on daily; "Assign accountable owners and deliverables"; "Align with
  stakeholders on timelines"; decision frameworks and RACI in personal notes.
- Meeting choreography: "17-25 min: Remediation decisions", header blocks with Purpose,
  Duration, Prepared by, Attendees.

Fix: write what the author actually wants from this reader, in the author's position
(see `context-cases.md`).

## 14. Procedural self-report [WP]

When the model reports on its own edit: "Revised for clarity while preserving the
original meaning", "ensured that all details are retained", "streamlined and refined".
In a change note, say what changed in content: "Added the October failure count, removed
the cost section."

## 15. Vague attribution and borrowed authority [WP]

"Industry experts agree", "studies show", "it is widely recognized", "best practice
suggests". Name the source or state it as the author's own view ("I think", "In my
tests").

## 16. Structure-level tells (manual) [WP][M][D]

The scanner can't see these. Check by reading.

- Every section has the same shape: one framing sentence, three bullets, one wrap-up.
- The opening paragraph is background; the actual news is in paragraph three.
- A "Challenges" or "Risks" section that names generic risks and closes with "Despite
  these challenges, ..." [WP].
- Balanced pros-and-cons tables where the author has an opinion and should state it.
- Paragraphs that can be reordered without changing anything: they don't build on each
  other.
- Every claim is safe and general; nothing is specific to this team, this system, this
  month.

## Manual checklist (when the scanner can't run)

Go through the text with these questions, line by line:

1. Any assistant phrases, placeholders, or `utm_source` links? (section 1)
2. Any sentence that says something is important, crucial, a milestone, or "matters"
   without a number? (2)
3. Any ", -ing ..." tail commenting on the sentence? (3)
4. Any "serves as", "stands as", "represents", "boasts"? (4)
5. Any "not X but Y", "it's not X, it's Y", more than one "rather than", "does not
   establish", "should be treated as"? (5)
6. Any "The result?", "Here's why", "The bottom line"? (6)
7. Any purpose statement at the start or summary at the end? Any "It's worth noting"? (7)
8. Lists of three that are rhythm rather than content? (8)
9. Words from the vocabulary lists? Count them; three or more in one page is a cluster. (9)
10. Stacked hedges? (10)
11. Bold labels on bullets, bold in prose, headings in a short text, em dashes, emoji? (11)
12. Sentence lengths all similar, or a run of short "This/It" sentences? (12)
13. Does the author sound like a consultant, auditor, or customer service? (13)
14. Every number, name, identifier, and link from the source still present, and nothing
    new that the user didn't supply? (Hard rules)
15. Every claim at the same status and certainty as in the source? Did a limitation ("does
    not show") turn into a finding, or a proposal into a promise? (Hard rules)
16. Does the text claim work was done (tested, validated, sent, migrated) that the source
    doesn't report? (Hard rules)
