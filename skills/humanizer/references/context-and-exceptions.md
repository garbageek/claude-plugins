# Context and exceptions

Choose the communication job before choosing an edit. A scanner match is a candidate
to inspect. Identify what that span does for this reader, what would improve, and
what the change could remove. If no defect is established, keep the text.

## Contents

- [Decision order](#decision-order)
- [Genre routing](#genre-routing)
- [Professional context](#professional-context-is-part-of-meaning)
- [Surface features](#context-gates-for-surface-features)
- [Language and feedback](#language-brevity-and-corrective-feedback)

## Decision order

Preserve meaning, evidence, criticism, uncertainty, and action status. Honor the
requested operation, length, audience, format, and explicit voice preferences. Use
comparable samples to resolve stylistic choices; apply generic preferences last.
An explicit format change authorizes that restructuring, not invented facts or
hidden loss of a material qualification.

**Generally applicable** rules address a defined defect, such as a reversed claim
or editing instructions left in a finished message. They still need their stated
trigger. **Context-dependent** rules require a reason from the genre, reader,
purpose, or demonstrated voice. Neither class establishes AI authorship.

An unsupported substantive assertion is not disposable filler. Preserve it and
flag the evidence gap separately unless the user authorizes a factual correction
or its omission. A missing measurement does not make a qualitative claim empty.

## Genre routing

| Context | Prioritize | Preserve when useful | Avoid imposing |
|---|---|---|---|
| Email, chat, status update | News or request, necessary reason, actual ask | Real courtesies, concise shared context, author-used contractions | Report ceremony, fake reassurance, invented urgency |
| Technical or product reference | Behavior, prerequisites, limits, exact terms | Tables, lists, headings, warnings, repeated identifiers | Synonym cycling, invented examples or capabilities |
| Scientific or research prose | Claim–evidence alignment, methods, scope, uncertainty | Passives, definitions, notation, abstracts, supported comparisons | Stronger causality, invented actors, arbitrary compression |
| Pull-request description or release note | Why the change exists, affected behavior, actual status | Before/after narration, migration details, actual checks | Claims of deployment or successful tests not established by the source |
| Proposal or decision memo | Recommendation, alternatives, evidence, costs, confidence | Meaningful headings, real trade-offs, required decision fields | Fake balance, status-quo pressure, unsolicited owner matrices |
| Public-relations or marketing copy | Accurate claims and requested brand register | Authorized persuasion, attributed quotations, genuine calls to action | Invented benefits, endorsements, measurements, or superlatives |
| Essay or article | Argument, progression, evidence, intended stance | First person, logical transitions, rhetorical contrast, recurring motifs | Generic directness that erases the argument or voice |
| Personal, social, or creative text | Authored experience, narrative logic, perspective, intended effect | Humor, fragments, repetition, metaphor, expressive punctuation, useful tags | Fabricated feelings or biography, compulsory lessons, engagement bait |

Infer whether “PR” means pull request or public relations from the material. If the
distinction remains material and unclear, preserve the current genre and flag it.
For evidence-heavy work, use [technical and scientific writing](technical-and-scientific-writing.md).

## Professional context is part of meaning

Separate speaker, recipient, relationship, shared knowledge, purpose, and authority.
A senior title establishes neither unfamiliarity with the system nor a preference
for formal language. A contributor can make a firm recommendation without assigning
work. A manager can need background without being nontechnical.

Keep speech acts distinct: observation, question, option, plan, promise, decision,
and completed action. “I” and “we” retain their referents. Keep criticism at its
supported strength; make a tone change without reversing the assessment. Questions
must express real uncertainty, not a consulting template's invented ownership gap.

Retain actual implementation and migration costs in comparisons. An existing
implementation is relevant evidence only when the stated decision depends on it;
its existence alone does not establish merit. Do not manufacture equal alternatives
when the supplied evidence favors one. See [context cases](context-cases.md) for
worked role, relationship, authority, and feedback failures.

| Requested artifact | Required boundary |
|---|---|
| Private notes or speaking points | Keep reminders and actual questions; add no attendee instructions or ceremonial metadata. |
| Private meeting brief | Keep supplied context and goals; invent no stakeholder motives or negotiating positions. |
| Shared agenda | Keep topics and preparation needs; a meeting duration alone does not authorize time slots or a chair. |
| Minutes or action log | Record what occurred and remained open; include owners and dates only when established. |
| Workshop running order | Keep actual timings; label any authorized newly proposed structure as proposed. |
| Required template | Preserve its useful fields; missing facts remain missing. Intentional blanks and redactions can be legitimate. |

## Context gates for surface features

| Candidate | Keep it when | Edit only when |
|---|---|---|
| Passive voice or nominalization | The actor is unknown, secondary, withheld, or the method is the focus | A known, relevant actor is obscured; never invent “we” to make a sentence active |
| Hedges and qualifiers | They encode probability, politeness, sampling, causal limits, approximation, or conditions | Multiple words duplicate the same function without changing certainty |
| Triads, parallelism, repeated openings | Items are distinct, entries comparable, procedures ordered, or rhetoric intentional | Padding or repetition demonstrably impairs the intended passage |
| Dashes, quotes, semicolons, compounds | Grammar, house style, voice, quotations, or technical notation require them | A specific parsing or consistency problem exists; no blanket punctuation ban |
| Headings, bullets, tables, emphasis | They aid navigation, accessibility, comparison, warnings, or retrieval | They obstruct the requested format or add empty ceremony; no word-count prohibition |
| Repetition and summaries | Terms stay consistent or the section serves a different reader or purpose | It repeats meaning without a distinct function, condition, or consequence |
| First person, humor, opinions | They belong to the author or an authorized fictional voice | The draft invents an experience, attitude, intimacy, or narrator |

Sentence-length variation is not a quota. Clear prose does not need deliberate
errors, irregularity, slang, or fragments to appear natural.

## Language, brevity, and corrective feedback

Apply the target language's grammar, typography, and idiom. English vocabulary
lists do not justify Russian or Ukrainian word bans. Preserve correct local dashes,
diacritics, mathematical Unicode, and meaningful joiners or nonbreaking spaces.
Clear second-language English does not need native idioms. Do not infer identity
or fluency from a passage; keep an uncertain construction when there is no sound
linguistic reason to change it.

A short-message request is a real constraint. Put the answer and its essential
condition together, keep the needed reason and ask, and omit background only when
authorized. Do not hide a material qualification to meet a target length.

When feedback rejects the role or genre, repair that framing before another cosmetic
pass. Inspect other affected passages, retain accepted edits, and apply explicit
corrections for the rest of the task. Use [voice calibration](voice-profile.md) for
sample-based preferences. Do not silently persist samples or a voice profile.

Match the destination: copy-ready text normally needs no “Revised version” wrapper;
a requested Markdown document, company template, or machine-readable payload keeps
its required structure. Place consequential audit notes outside the author's text.
