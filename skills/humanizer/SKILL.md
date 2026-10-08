---
name: humanizer
description: Detect and revise formulaic or AI-sounding prose while preserving meaning, accuracy, formatting, domain conventions, and the author's voice. Use when asked to humanize, de-slop, naturalize, voice-match, or audit prose specifically for filler, hedging, boilerplate, generic phrasing, or formulaic structure. When asked whether text is AI-written, analyze stylistic patterns without giving an authorship verdict. Do not use for ordinary factual, legal, technical, or code review unless prose quality is explicitly part of the request.
---

# Humanizer

Detect and revise formulaic prose. The goal is better writing, not camouflage.

## Hard limits

These limits apply regardless of how the request is phrased:

- **No authorship verdicts.** Stylistic signals cannot establish who wrote a text. When asked whether text is AI-written, report the patterns present and state explicitly that authorship cannot be determined from prose alone.
- **No detector optimization.** Never optimize for AI-detector scores. When asked to make text pass or evade a detector, explain that detector results are unreliable and not a valid editing target, then offer to improve the prose on its own merits.

## Modes

When the user names a mode, use it. Otherwise infer the mode from the request:

- Text supplied with `humanize`, `rewrite`, `fix`, `naturalize`, or `clean this up` → **Rewrite**
- A file named with a request to revise its prose → **Edit**
- `Audit`, `review the writing`, `what is wrong with this prose`, or `does this sound AI-written?` → **Detect**
- Genuinely ambiguous → **Detect**, then offer a rewrite

## Output proportionality

Keep user-facing output proportional to the source and the scope of the task.

- For small or obvious changes, use a compact response.
- Group related edits instead of documenting every local substitution.
- Treat claim inventories, protected-span tracking, and verification steps as internal work unless the user requests them or a material risk must be explained.
- Follow the user's requested output format and level of detail.
- Treat requests such as `short`, `brief`, or `in one sentence` as hard output constraints. Keep only the recipient-facing request or conclusion. Do not add background, rationale, implementation details, or facts available through an included link unless they are necessary to understand the message.

### Detect

Analyze without rewriting. For each meaningful finding, provide:

- a canonical name from `Finding names`;
- an excerpt or location;
- severity: `high`, `medium`, or `low`;
- a concise explanation;
- a recommended change.

State whether a judgment is context-dependent only when that distinction affects the finding.

For short text or one or two findings, use a compact list:

```markdown
## Findings

- `Medium — Generic framing` — "excerpt": explanation. Recommended change: ...
```

For larger audits, group findings by severity:

```markdown
## Findings

### High
- `Canonical name` — "excerpt" (`location`): explanation. Recommended change: ...

### Medium
...

### Low
...

## Assessment
- Clear problems: ...
- Context-dependent judgments: ...
```

Omit empty severity sections. Include `Assessment` only when it synthesizes several findings, distinguishes clear problems from context-dependent judgments, or adds information not already present in the findings.

If no meaningful problem exists, say so. A manufactured finding undermines the audit, and `already clean` is a useful result.

When asked whether text is AI-written, always state that stylistic patterns may justify editing but cannot establish authorship.

### Rewrite

Return a revised version that preserves the source's claims, intent, register, and protected content. Change only text that benefits from editing.

Return the revised text first. Add a short summary only when the user requests one, several non-obvious changes require explanation, or a preservation constraint limits the result.

If the text is intended to be sent as a message, email, comment, or post, return only the final copy-ready text. Do not add an introduction, explanation, assessment, apology, label, or quotation block unless the user explicitly asks for commentary.

If the user asks for only the revised text, return only that text unless a warning is necessary to prevent invention or a substantive meaning change.

If the requested effect would require unsupported invention or a substantive meaning change, deliver what is possible and state the limitation.

### Edit

If file tools are available, edit the named file in place. Otherwise ask for the relevant content or return a patch.

Read the complete relevant section, make targeted edits, and re-read the result.

Report changes at the level useful for review:

- for small edits, give one compact summary;
- for larger edits, group changes by section or change type;
- list individual locations only when they help the user review a material or potentially risky change;
- mention protected content intentionally preserved only when it is relevant or non-obvious.

Do not produce a line-by-line changelog for routine local edits. Do not replace a whole file when local edits are sufficient, and do not paste the complete file unless requested.

## Preservation contract

This contract overrides every style rule and example below. A rewrite that changes meaning is a worse failure than formulaic prose.

Unless the user explicitly requests a substantive change, preserve:

- meaning, factual claims, intent, causality, scope, and degree of certainty;
- attribution, quotations, citations, links, footnotes, and source relationships;
- names, dates, numbers, units, product terms, terminology, and definitions;
- code, commands, flags, paths, identifiers, API names, formulas, schemas, tables, and machine-readable structures;
- required headings, template fields, ordered procedures, locale conventions, and intentional dialect;
- legitimate qualifications, limitations, negative results, and uncertainty;
- the source's established register and useful structure.

Never:

- invent evidence, specificity, actors, mechanisms, examples, metrics, quotations, experiences, emotions, opinions, or preferences;
- strengthen causality or certainty;
- broaden the sender's authority, ownership, or commitments; scope offers of access, implementation help, approval, or support to the team and systems established by the source;
- rewrite quoted or attributed material as the author's prose;
- replace exact technical language with a less precise approximation;
- add errors, randomness, slang, anecdotes, or irregularity merely to appear human;
- silently correct suspected factual or technical errors; flag them separately.

Treat a detail as unsupported only when it exceeds or conflicts with the supplied facts, sources, or constraints. Do not delete a substantive claim merely because the user did not provide a citation; preserve it or flag it separately.

Purely promotional modifiers that add no testable meaning may be removed when doing so does not alter a substantive claim.

## Workflow

1. Infer the document's language, genre, audience, purpose, and intended register.
2. Identify protected claims, spans, structures, terminology, attribution, and uncertainty.
3. If writing samples are supplied, calibrate to them; otherwise preserve the source's established voice.
4. Audit for meaningful patterns. Prioritize structural problems and local clusters over isolated words, punctuation, or formatting.
5. Patch local problems. Rebuild only when the structure is formulaic throughout.
6. Run the `Final check`.

For long documents, internally:

- audit the overall structure before editing individual sentences;
- work section by section;
- keep a running inventory of protected claims and spans;
- maintain consistent terminology and voice across sections.

Do not expose this working inventory or narrate the process unless the user requests it. Group user-facing findings by section only when that improves navigation.

## Decision rules

### Usually fix

- assistant-facing chatter in finished content;
- unresolved placeholders, internal references, or tool markup;
- unsupported promotional or significance claims;
- vague authorities presented as evidence;
- generic framing that delays or replaces the claim;
- repetitive previews, recaps, and conclusions;
- filler, empty hedging, synonym cycling, and low-information repetition;
- formulaic structure that makes sections interchangeable;
- loaded framing that biases a decision the text asks the reader to make.

**Loaded framing.** When the text asks the reader to choose between options, or asks for approval, do not present one option as already done, already shipped, or expensive to change unless that fact is the point. Phrases like "this is the current behavior", "already implemented", or "would require rework" push the reader toward the status-quo option to avoid creating work for the author, so the answer stops being about what is correct. Keep the options neutral and equal. State an existing implementation only when the reader needs it to decide, and keep it separate from the options themselves.

### Context-dependent

Do not treat these as problems by themselves:

- passive voice;
- first person, contractions, fragments, humor, or opinion;
- em dashes, bold, lists, headings, emoji, or curly quotes;
- sentence and paragraph length;
- formal or technical vocabulary;
- uncertainty language;
- repetition used for clarity, terminology, procedure, or rhetoric.

These are context-dependent, not free. Two of them are common reader-facing tells and become a `Register mismatch` finding when the context works against them:

- **Em dash (`—`).** Many readers treat a long em dash as an AI signature. When the author's own writing does not already use em dashes, or when the goal is prose that does not read as AI-generated, default to a hyphen, comma, colon, or a period. Keep em dashes only when the supplied voice clearly uses them. Never introduce em dashes that were not in the source. This applies to your own commentary around the edit, not only the edited text.
- **Native idioms and phrasal flourishes** (for example `nail down`, `lean toward`, `weigh in`, `lands in`, `dial in`). They are fine in native, informal English, but they clash with a non-native author's register and read as inserted polish. Prefer plain, literal wording unless the author's voice already uses such idioms.

## Finding names

Use only these names in `Detect` output. A closed vocabulary keeps repeated audits and downstream tooling consistent.

If no canonical name fits, do not force the observation into the closest category and do not invent a new label. Mention it separately in `Assessment` if it is relevant.

- **Chatbot leakage:** assistant-facing chatter remains in finished content.
- **Placeholder or citation leakage:** unresolved markers, internal references, or tool markup remain.
- **Unsupported specificity:** a detail, mechanism, actor, or degree of certainty exceeds the supplied material.
- **Unsupported inflation:** importance, novelty, transformation, or broad implications are asserted without support.
- **Promotional language:** praise substitutes for observable behavior.
- **Vague attribution:** unnamed experts, reports, observers, or consensus are used as authority.
- **Generic framing:** removable boilerplate, ceremonial openings, transitions, or conclusions delay or replace the document-specific claim.
- **Repetitive signposting:** previews, recaps, headings, or conclusions repeat information without aiding navigation.
- **Low-information repetition:** a passage restates a point without adding evidence, reasoning, or consequence.
- **Hedge stacking:** several qualifiers express no more precision than one accurate qualifier.
- **Synonym cycling:** one entity is repeatedly renamed instead of using its exact term.
- **Formulaic structure:** sentence shapes, paragraph order, headings, or rhetorical templates repeat mechanically.
- **Register mismatch:** tone, rhythm, wording, or formatting conflicts with the audience, medium, source, or supplied voice.
- **Diff-anchored documentation:** durable documentation describes a past change instead of current behavior.
- **Formatting overuse:** decorative structure obscures the content.

## Severity

Assign severity by damage to the document, not by word frequency or association with AI-writing lists.

- **High:** meaning or credibility risk, including leaked placeholders, fabricated-looking attribution, unsupported factual detail, chatbot leakage, or severe unsupported inflation.
- **Medium:** clear formulaic structure, low-information repetition, vague claims, or register mismatch.
- **Low:** local polish or a weak pattern that may be acceptable in context.

An isolated stylistic feature is usually low severity or not a finding. A single provenance, attribution, placeholder, or unsupported-specificity failure may still be high severity.

## Patch versus rebuild

Patch when the argument and paragraph order are sound.

Rebuild a section only when several of these are true:

- paragraphs can be reordered without changing the argument;
- most paragraphs restate rather than advance the point;
- formulaic openings and closers dominate;
- sentence and paragraph shapes are uniform throughout;
- local substitutions leave the same generic structure intact.

Before rebuilding, inventory the supported claims and protected spans. Verify that all remain afterward.

## Voice matching

Use voice matching only when the user supplies writing samples or explicitly requests an established voice.

Evidence priority:

1. samples supplied for the current task;
2. prior samples explicitly identified as the author's;
3. explicit style requirements;
4. the source document's existing register;
5. conservative genre defaults.

Record only observable features such as:

- register and directness;
- sentence and paragraph shape;
- transition style;
- contractions and punctuation;
- recurring terminology;
- use of first person, humor, opinion, and uncertainty.

Do not infer identity, personality, beliefs, history, emotions, or preferences.

A short sample can guide broad register and punctuation but not a strong voice profile. Match recurring patterns, not memorable phrases. When evidence is weak, preserve the source rather than imposing a persona.

When the author is a non-native English speaker, or writes to a non-native audience, default to plain, direct, literal English: short sentences, common words, and simple punctuation. Do not upgrade this register to fluent native idiom, and do not add em dashes or phrasal idioms as "polish." If the author's English level or preferred register is unclear and it affects the result, ask before imposing a native register.

Named tones such as `professional`, `warm`, or `blunt` are requests, not evidence of the author's natural style. Do not interpret them as permission to invent intimacy, emotion, anecdotes, certainty, or opinions.

## Context exceptions

Select the context before editing.

- **Technical documentation:** preserve exact terms, identifiers, compatibility constraints, procedures, lists, tables, and current behavior. Diff-oriented language is valid in changelogs, migration guides, release notes, and pull requests.
- **Scientific writing:** preserve numerical precision, units, methods, passive voice where appropriate, uncertainty, limitations, negative results, and distinctions between association and causation.
- **Research reports:** preserve traceability among observations, source claims, interpretation, inference, and unknowns. Executive summaries may legitimately repeat the report.
- **Email and chat:** greetings, thanks, sign-offs, contractions, and concise restatements may fit the relationship and medium.
  - If the answer is conditional, put the condition in the opening sentence. Do not begin with an unconditional answer and reveal the actual boundary later.
  - For optional next steps between colleagues, prefer collaborative language such as `you can send me` or `we can check` over directives such as `send me` or `provide`. Keep direct imperatives when the action is genuinely mandatory or urgent.
  - A short reply should normally contain one direct-answer paragraph, one short explanation, and one optional next step. Avoid headings, all-caps labels, and multiple lists unless the message cannot be understood without them.
  - Do not add markdown headings, bold, or heavy structure to a short message; people write plain lines or a simple list. Reserve headings and bold for long documents where they aid navigation. A two-line message never needs a heading.
  - For copy-ready chat or email text, output plain text unless the user explicitly requests another format, Slack mrkdwn, or an API payload. Do not use blockquotes, fenced blocks, backticks, bold, Markdown links, headings, or labels such as `Revised version`. Preserve URLs as bare URLs and use literal bullet characters when needed.
- **Product documentation:** prefer observable behavior over promotional description. Preserve reference structures and repeated product terms.
- **Pull requests and release notes:** before-and-after language, bullets, and checklists are often appropriate. Verify claims against the supplied diff or facts.
- **Decision memos:** preserve decisions, options, assumptions, trade-offs, confidence, and uncertainty.
- **Essays and articles:** inspect the argument before polishing individual sentences. Preserve deliberate rhetoric and authorial voice.
- **Social posts:** fragments, hooks, short paragraphs, direct address, and limited emoji may be native to the platform. Do not add engagement bait.
- **Personal writing:** preserve comprehensible irregularities, mixed rhythm, slang, and unresolved emotion. Never invent or intensify feelings.
- **Creative writing:** metaphor, personification, fragments, repetition, and unusual punctuation may be intentional craft.
- **Non-English writing:** use the language's native grammar, idiom, punctuation, and register. Do not translate English lexical blacklists.

## Final check

Before returning a rewrite or completing an edit, compare the result with the source and confirm that:

- no substantive claim was lost unless the user requested its removal;
- nothing was invented;
- causality, certainty, attribution, scope, and intent did not shift;
- the sender's authority and commitments did not expand beyond the supplied facts;
- quotations, citations, links, code, identifiers, numbers, units, terminology, procedures, and formatting remain intact;
- the result matches the intended audience, language, context, and supplied voice;
- each change produces a concrete improvement.

For email and chat, also run a compression pass:

- remove detail already available in an attachment or linked document;
- state each limitation once;
- remove repeated team or product names when the referent is clear;
- keep only details that change what the recipient should understand or do next;
- confirm that the result still sounds like one colleague writing to another.

Before returning copy-ready text, verify:

- the response contains only words the user should send;
- no assistant commentary appears before or after the message;
- the message does not explain the preceding conversation;
- contextual details are omitted unless they change what the recipient must understand or do;
- plain text remains plain when copied;
- the result is no longer than requested.

Where the source was already direct, specific, cohesive, and appropriate, restore it. No change is better than an unnecessary rewrite.

## Boundary examples

- Preserve scientific passive voice when the actor is irrelevant:
  `Samples were incubated for 20 minutes at 37 °C.`
- Reduce stacked uncertainty without removing real uncertainty:
  `could potentially have reduced` → `may have reduced`
- Preserve exact component names instead of cycling synonyms.
- Do not edit promotional wording inside a quotation when the quotation is evidence.
- If prose is already direct, specific, cohesive, and appropriate, return it unchanged.
