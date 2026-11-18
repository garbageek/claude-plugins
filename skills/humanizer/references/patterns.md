# Editorial patterns and scanner candidates

The scanner locates possible surface patterns. Its HIGH/MEDIUM/LOW values describe
heuristic signal strength, not authorship probability or the consequence of an edit.
Use the consequence-based severity in `SKILL.md` for confirmed findings.

Source provenance and design limits are recorded in [SOURCES.md](../SOURCES.md).
The vocabulary and rhythm heuristics are not validated authorship tests. Retained
scanner category names appear in backticks; manual checks have no automatic coverage
unless explicitly stated.

## Navigation

- [Residue and unsupported framing](#1-chatbot-leakage-and-placeholders): 1–3.
- [Wording, rhetoric, and uncertainty](#4-copula-avoidance): 4–10.
- [Format, rhythm, role, and structure](#11-formatting-and-punctuation): 11–16.
- [Additional manual checks](#additional-manual-checks): exact terms, voice, logic,
  conditions, artifact type, evidence attachment, language, and rendering.
- [Manual checklist](#manual-checklist).

## Apply a rule

For each candidate, identify the exact span, its function, a demonstrated defect,
and the smallest safe change. Check [context and exceptions](context-and-exceptions.md)
first when genre or voice could justify it. Merge overlapping findings about one span.

**Generally applicable** means a defined defect usually needs repair or a separate
flag. **Context-dependent** means changing the span needs affirmative evidence from
its use. Neither class means a phrase should be deleted on sight. A substantive
unsupported claim stays in supplied text and gets a separate evidence flag unless
its correction or omission is authorized. Draft only from supplied facts.

## 1. Chatbot leakage and placeholders

**Class:** Generally applicable after confirming the material is finished prose
for another reader. **Scanner:** `chatbot-leakage`, `placeholder`.

Candidates include “Here's the revised version,” “As a language model,” offers to
rewrite again, unresolved fields, and tool-specific citation markers. Remove editing
conversation from a finished artifact. Retain a real greeting, sign-off, offer to a
colleague, transcript, quotation, or requested disclosure.

Fill an unresolved field only from supplied information. If a required fact is
missing, retain its marker and flag the gap; do not invent it or claim completion.
Intentional fillable templates, redactions, and code placeholders may remain.

Repair a citation marker only with an available source mapping. Otherwise retain
it and flag the missing attribution. A valid footnote marker is not leakage. Keep
URLs exact, including `utm_source` or other query parameters; style editing does
not authorize stripping them.

## 2. Puffery and significance inflation

**Class:** Context-dependent; an unsupported factual escalation is a generally
applicable evidence concern. **Scanner:** `puffery`.

Inspect “plays a crucial role,” “significant milestone,” “paving the way,” “valuable
insights,” and “This matters” for emphasis that replaces or duplicates the supplied
point. Preserve genuine importance, attributed opinion, warning strength, and the
requested persuasive register. A number is not required for every qualitative claim.

- Source: “This important warning is of great importance: keep the lid closed.”
- Edit: “Warning: keep the lid closed.”

“First ever,” “significantly reduces failures,” and “guarantees reliability” assert
something substantive. Keep and flag an unsupported claim rather than deleting it
as filler or inventing a benchmark to justify it.

## 3. Participle tails and interpretive gloss

**Class:** Context-dependent; an unsupported inference needs a separate evidence
flag. **Scanner:** `participle-tail`, sometimes `puffery`.

Constructions such as “, ensuring…,” “, highlighting…,” “, что позволяет…,” or
“, забезпечуючи…” can carry a real mechanism, consequence, or interpretation.
Grammar alone is no defect. Remove a tail only when its meaning is already covered
or the user authorizes dropping it.

“The label is blue, proving that users trust it” contains an unsupported inferential
claim. Flag the link; silently reducing it to “The label is blue” would remove a claim.
A supported explanation such as “The latch holds the lid shut, preventing it from
opening” can stay unchanged.

## 4. Copula avoidance

**Class:** Context-dependent. **Scanner:** `copula-avoidance`.

Simplify “serves as,” “acts as,” “represents,” or “boasts” only when a simpler verb
expresses exactly the same relation. Keep temporary functions, representation,
symbolism, and domain-specific roles.

- “The title serves as the heading of the note” → “The title is the heading of the
  note,” when the source establishes identity.
- Keep “The standby node acts as the leader during failover”; replacing a conditional
  role with unconditional identity could change the behavior.

## 5. Negative parallelism and corrective framing

**Class:** Context-dependent. **Scanner:** `negative-parallelism`, `corrective-disclaimer`.

“Not just X, but Y,” “rather than,” and similar contrasts can be empty drama or real
exclusions. Preserve both sides when they convey distinct meaning. Repeated use is
an inspection cue, not a prohibition. Russian and Ukrainian contrasts need the same
meaning check in their own grammar.

“The experiment does not establish causality” is a valid evidence boundary and may
need no edit even when the scanner flags it. The same applies to “based on available
evidence,” “not publicly documented,” and genuine as-of or methodological limits.

A permitted shorter version of “Late events were rare in October. The October test
does not establish that late events are rare in general” is “Late events were rare
in October; that result does not establish that they are rare in general.” Both the
observation and the generalization limit survive. Leaving the source unchanged is
also valid.

## 6. Setup-reveal and rhetorical Q&A

**Class:** Context-dependent. **Scanner:** `reveal-framing`.

Inspect repeated “The result?”, “Here's why,” and immediate question/answer reveals
when they delay a routine update or make a reference harder to scan. Keep actual
questions, FAQs, teaching prompts, and intentional narrative suspense.

“The next step? Close the lid” → “Next, close the lid” preserves the supplied action.
Do not replace a vague result with a new deadline, measurement, or benefit.

## 7. Signposting, purpose statements, and wrap-ups

**Class:** Context-dependent; true duplication without a separate function is a
generally applicable editing defect. **Scanner:** `signposting`, `purpose-statement`,
`wrap-up`.

Candidates include “This document outlines…,” “It's worth noting,” “Let's dive into,”
“Overall,” “In conclusion,” «важно отметить», and «варто зазначити». Remove a frame
when it only announces or repeats the point immediately available. Preserve actual
scope, a necessary warning, a logical conclusion, or useful document navigation.

A report can have an abstract and a conclusion serving different readers or purposes.
A closing assertion is not disposable just because it appears after “Overall.”
Consolidate repeated meaning without losing added conditions or stance.

## 8. Rule of three and artificial symmetry

**Class:** Context-dependent. **Scanner:** `rule-of-three`.

Inspect equal-sized sections and adjective triads for duplicate content. Keep all
distinct properties, requirements, steps, and comparisons; their count is irrelevant.

“The note is brief, short, and concise” can become “The note is concise” when the
adjectives repeat the same property. “Keep the name, type, and default” keeps all three
fields. Deliberate parallel rhetoric and consistent reference entries can remain.

## 9. Vocabulary clusters and modifier stacks

**Class:** Context-dependent. **Scanner:** `ai-vocabulary`, `ai-vocabulary-cluster`,
`vocabulary`, `officialese`, `idiom`.

Inspect clusters of abstract praise or familiar corporate phrasing where a clearer
expression of the existing claim is available. Examples include “leverage,” “robust,”
“streamline,” “holistic,” “actionable,” “delve,” “tapestry,” “circle back,” «данный»,
«в рамках», «комплексный», «здійснювати», and «у рамках». Ordinary words such as
“practical” or “clearer” remain ordinary words even when a heuristic lists them.

Do not treat these lists as substitutions or translated blacklists. Keep field terms,
proper names, quotations, literal meanings, and the author's established diction:
“primary key,” “robust estimator,” “landscape orientation,” and “statistically
significant” are legitimate concepts.

“Utilize the list to facilitate finding the entry” can become “Use the list to find
the entry.” Rewrite an unclear modifier stack using supplied meaning; preserve
necessary distinctions and compounds such as “read-only” and “error-correcting.”

## 10. Hedging

**Class:** Context-dependent. **Scanner:** `hedge-stacking`.

Remove only duplicated softening. “The lid might perhaps be loose” can become “The
lid might be loose” when both words express the same uncertainty. It cannot become
“The lid is loose.” Politeness, statistical uncertainty, approximation, conditions,
and sampling limits may each do different work. The number of qualifiers is not a
measure of the strength of a claim.

## 11. Formatting and punctuation

**Class:** Context-dependent. **Scanner:** `inline-header-list`, `bold-overuse`,
`formatting-overuse`, `title-case-headings`, `emoji`, `em-dash`, `curly-quotes`,
`punctuation-monotony`.

Judge formatting by its function: navigation, comparison, emphasis, accessibility,
warning, procedure, or retrieval. Preserve required templates, useful labels, ordered
steps, reader-friendly headings, and authored emoji. A short document is not exempt
from having structure; a long one does not need decorative sections.

Repair nested interruptions or mixed typography that cause an actual reading problem.
Do not remove every dash or insert semicolons merely to vary punctuation. English,
Russian, and Ukrainian dashes can all be legitimate. Keep quotation punctuation and
mathematical symbols exact.

For a requested plain chat message, “## Request / **Please** review the **draft**” can
become “Please review the draft.” That is a destination-specific edit, not a global
ban on headings or bold text.

## 12. Rhythm

**Class:** Context-dependent. **Scanner:** `uniform-rhythm`, `staccato`,
`demonstrative-chain`, `uniform-paragraphs`, `repeated-opener`.

Inspect repeated sentence shapes when they hide relationships, overemphasize minor
points, or conflict with the demonstrated voice. Join related clauses or divide an
overloaded sentence to repair that specific problem. Do not aim for a target average,
variance, or sentence-length band.

Keep short instructions, parallel comparisons, reference entries, deliberate fragments,
and authored repetition. “Read the label. Then check the lid” need not change merely
because both sentences are short. Never add random fragments or errors for variation.

## 13. Service and consultant register

**Class:** Context-dependent. **Scanner:** `service-register`, `role-drift`, `idiom`.

An insider may be miscast as an outside auditor; personal talking points may gain a
facilitated agenda; a contributor's request may become “Assign accountable owners.”
Restore the actual speaker, relationship, shared knowledge, and artifact. See
[context cases](context-cases.md).

Genuine customer-service obligations, thanks, encouragement, and offers to help can
stay. A technical manager's title does not justify stripping technical detail. Do not
make a legitimate recommendation timid to avoid sounding managerial.

## 14. Procedural self-report

**Class:** Generally applicable when editing narration leaks into finished copy or
a new completed-work claim lacks support. **Scanner:** `procedural-self-report`;
work-status accuracy also requires manual review.

Remove “Revised for clarity while preserving meaning” from the author's message.
Keep requested methods, actual change notes, relevant limitations, and truthful
verification records outside copy-ready text when appropriate.

“Ready for review” must not become “reviewed and approved.” Report a file save,
scan, test, deployment, or send only when supported by source facts or actual observed
work. A style edit establishes none of those actions by itself.

## 15. Vague attribution and borrowed authority

**Class:** Generally applicable when required attribution is untraceable. **Coverage:** manual.

“Studies show” or “experts agree” needs a source appropriate to the document. Use
an already supplied citation or flag the missing attribution. Do not invent an expert,
assume the claim false, or recast it as “I found” or “In my tests.” Contextualized
anonymous sources, confidentiality constraints, and informal reporting can be valid.

Keep bibliographies, literature inventories, and relevant source lists. In explanatory
prose, a list of prestigious names does not itself explain a claim; flag missing
relevance without inventing what those sources found.

## 16. Structure-level patterns

**Class:** Context-dependent. **Coverage:** manual, assisted by surface candidates.

Inspect repeated section molds, a buried request, generic challenge-and-optimism arcs,
or paragraphs that do not develop the intended argument. Rebuild from the fact sheet
when the role, artifact, argument order, or organization is actually wrong. Patch
local defects; preserve accepted or already effective prose.

Consistent reference entries, independent FAQs, required risk sections, and deliberate
narrative pacing are legitimate exceptions. A balanced comparison can be useful; it
becomes a problem when the edit hides the author's recommendation or invents equal
merit. Keep unsupported forecasts and flag them instead of replacing them with
plausible risks or success metrics.

## Additional manual checks

These cover defects not reliably recognized by the scanner. Use a specific name from
this table for a confirmed manual finding, or the established role/meaning labels
below. They are not new scanner category names.

| Pattern | Rule class and trigger | Safe action and exception |
|---|---|---|
| Terminology drift | Generally applicable when one established referent gets misleading new labels | Restore its exact term; preserve genuinely different components and deliberate literary variation |
| False range | Generally applicable when “from X to Y” asserts coverage or a scale not supplied | Flag unsupported coverage; name only supplied items when that narrowing is authorized; retain real ranges and figurative breadth |
| Undefined analytical label | Generally applicable when an unexplained coined framework, trap, or paradox stands in for an argument | Use its supplied definition or flag the missing one; keep established terms and defined fictional concepts |
| Missing or false logical bridge | Generally applicable when a connector or referent asserts an unsupported relation | Clarify an established relation; flag a missing inference instead of inventing “therefore”; keep deliberate juxtaposition |
| Invented experience or speculation | Generally applicable when the draft adds a motive, biography, feeling, opinion, or fact absent from source notes | Restore the supplied content; preserve authorized fiction or clearly identified hypotheses; flag unsupported claims already in the source |
| Buried material condition | Generally applicable when an opening answer appears unconditional despite a later prerequisite | Put the existing condition beside the answer; add no new prerequisite |
| Evidence or protected-content detachment | Generally applicable when a value, citation, actor, comparison, or negation attaches to the wrong claim | Restore the relationship and inspect meaning even if token counts match |
| Change narration in reference prose | Context-dependent when current behavior is the requested artifact | Use current behavior only within an established version scope and authorized history omission; keep change logs, PRs, and migration facts |
| Engagement bait or decorative imagery | Context-dependent when an added invitation, tag, analogy, or flourish serves no intended purpose | Remove empty or unauthorized additions; keep genuine invitations, useful tags, clear teaching analogies, and deliberate literary effects |
| Language-insensitive correction | Context-dependent when a translated blacklist or assumed native voice drives the edit | Use the target language and actual samples; preserve clear second-language register and required terminology |
| Rendering artifact | Context-dependent when an exact code point demonstrably breaks text or an identifier | Identify the character and normalize only within authorized scope; preserve valid diacritics, joiners, nonbreaking spaces, notation, and quotations |

For source-to-result meaning and professional-context findings, retain these labels:
**Role or relationship mismatch**, **Authority drift**, **Commitment drift**,
**Unsupported completed-work claim**, **Artifact mismatch**, **Shared-context mismatch**,
**Stance drift**, **Limitation drift**, and **Feedback regression**. Confirm each
against the source and task. A new owner, deadline, team agreement, softened criticism,
or repeated rejected framing matters more than any number of vocabulary hits.

## Manual checklist

When the scanner is unavailable, or after reviewing its candidates, check:

1. Is editing conversation, an unintended placeholder, or unresolved attribution left
   in finished copy? Keep valid template fields, full URLs, quotations, and citations.
2. Is any distinct claim, condition, uncertainty, attribution, or status added or lost?
   Compare what each sentence asserts, not just which words remain.
3. Does the speaker have the same relationship, authority, and shared context? Are
   questions, proposals, decisions, and completed work still distinct?
4. Does a candidate phrase, formatting choice, or rhythm cause a specific defect in
   this genre? If no, keep it even if the scanner marks it HIGH.
5. Are unsupported assertions preserved and flagged, with no invented fact, source,
   experience, actor, metric, or deadline added to make the prose specific?
6. Does each paragraph do its intended job? Keep functional structure and summaries;
   remove only real duplication and repair established logical relationships.
7. Do exact names, tokens, quotations, URLs, code, formulas, and their relationships
   survive? Inspect edit boundaries and the saved diff when editing a file.
8. Does the result honor the samples, latest feedback, required format, and length
   without reintroducing rejected framing or hiding a decisive limitation?

Stop when no justified correction remains. A clean scan is neither a goal nor proof
of preserved meaning, factual accuracy, a voice match, or human authorship.
