---
name: humanizer
description: Drafts, rewrites, and checks text that goes out under the user's own name (reports, status updates, design docs, proposals, emails, Slack messages, meeting notes, talking points for a manager or leadership) so it reads as written by that person and carries no AI tells. Use whenever drafting or editing such text, even if the user never says "humanize", and when asked to humanize, de-slop, remove AI smell, make text sound less like ChatGPT/GPT/Claude, rewrite in their voice, or check whether text reads as AI-written (also "очеловечь", "убери AI-стиль", "звучит как нейросеть"). Includes an advisory pattern scanner and a token-preservation check (Python 3, no dependencies). English, Russian, Ukrainian. Not for code review or fact-checking unless prose quality is part of the request.
metadata:
  version: "3.1.1"
---

# Humanizer

The user sends these documents to colleagues and management as his own work. Those
readers have seen a lot of ChatGPT output and recognize it from a few lines. The job is
text this author would plausibly write to this reader, with every fact, number, and
position intact.

## How this version works

The earlier versions missed the AI smell for three reasons, and the steps below exist to
close them:

1. They treated em dashes, bold labels, lists of three, and "AI words" as neutral style
   choices to be judged case by case. Readers detect AI text by exactly those surface
   patterns, so the smell survived. This version names the patterns and removes them
   by default (`references/patterns.md`).
2. The model checked its own output by impression. Its default style is the smell, so it
   cannot see it. This version runs a scanner (`scripts/ai_tells.py`) on every draft.
3. Rewriting sentence by sentence keeps the AI skeleton: the section layout, the bold
   lead-in bullets, the even rhythm, the closing summary. This version rebuilds from a
   fact sheet when the structure, role, or genre is wrong.

Drafting in the user's name, the role and genre checks, and the context cases come from
v2 and are kept.

The scanner is a tool for the editor, not a judge. Meaning, role, and commitments
outrank any pattern count (see "Severity").

## Hard rules

These override every style rule below. A rewrite that changes meaning is worse than one
that still smells.

- Keep every claim, number, unit, date, name, identifier, code span, link, quotation, and
  citation. Keep causality, scope, chronology, and the degree of certainty.
- Keep the author's position: criticism stays criticism, disagreement stays disagreement,
  a recommendation stays a recommendation. Don't soften it to sound diplomatic or sharpen
  it to sound confident.
- Keep the status of each statement. A finding stays a finding, a proposal stays a
  proposal ("we could" never becomes "we will"), an open question stays open, and a
  decision or commitment appears only if it was actually made.
- Never invent facts, reasons, owners, dates, approvals, anecdotes, feelings, or
  expertise. Unknowns stay unknown.
- Keep the limits of the evidence at their original strength. If the source says a test
  does not show something, the rewrite must not turn that into a finding; removing a
  recognizable phrase never justifies changing what is known.
- Claim only work that happened. "Tested", "validated", "migrated", "reviewed", "sent",
  "fixed" appear only when the source or the user says that action was done.
- Write from the author's real role. Don't turn an engineer reporting to his manager into
  a consultant, auditor, or executive who assigns owners and sets governance.
- Never add typos, slang, fake informality, or random fragments to look human. Remove
  the tells; don't add noise.
- Keep required formats: a template the company requires, a table the reader asked for,
  numbered steps in a procedure, code blocks.
- Do not silently correct suspected factual or technical errors while editing style.
  Preserve the source's claim and flag the concern separately; correct it only when
  the user asks for fact correction and there is supporting evidence.

## Workflow

### 1. Pin down the situation

Work this out from the conversation and files, silently. Don't print a questionnaire.

- **Author:** who signs it, their role, how involved they were in the work.
- **Reader:** who reads it, their relationship to the author, and what they already know.
  A direct manager who knows the system is a different reader from a VP who doesn't.
  A senior title doesn't mean the reader needs formal prose or less technical detail.
- **Purpose:** what the author wants after the reader finishes: a decision, approval,
  time, awareness of a risk, an answer.
- **Form:** channel and genre (see the table), language, length limit, required template.
  Treat "brief", "short", and "one sentence" as hard constraints on the delivered text.
  Keep what the reader needs; don't repeat detail already available in an attached or
  linked document unless the message is unintelligible without it. Never hide a
  material omission made for brevity.
- **Voice:** real writing samples by the author, if any exist in the conversation or
  project (for example a `voice-profile.md`; template in `references/voice-profile.md`).
  Never learn the author's voice from AI drafts, and don't assume the way he writes to an
  assistant is how he writes to his boss.

Ask one short question only when a wrong guess would produce a different document (for
example, unclear whether this is private prep notes or something the manager will read).
Otherwise pick the sensible reading and note it in one line.

| Intended use                       | Starting form                                                               | Don't add unless asked                                       |
| ---------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Private notes or talking points    | Short reminders, numbers, real questions, in speaking order                 | Header block, timeboxes, owner matrix, executive summary     |
| Status update or report to manager | The news first, then the evidence, then the ask                             | Purpose section, "Key findings" with bold labels, conclusion |
| Email or chat message              | Answer or ask in the first lines, needed context, one clear request         | Headings, bold, sign-off formulas, recap                     |
| Proposal or design doc             | Problem with numbers, the option chosen and why, cost, risks, what's needed | "Why it matters", "Overview", balanced pros/cons theater     |
| Shared agenda                      | Topics and what to prepare                                                  | Minute slots, chair, decision framework                      |
| Minutes after a meeting            | What was discussed, decided, and left open; owners only if assigned         | Decisions or owners nobody agreed to                         |
| Required company template          | The template, filled with real content                                      | Invented content to fill empty fields                        |

### 2. Build a fact sheet

Before writing, list for yourself (not for the user):

- every claim, number, date, name, identifier, link, and code span;
- for each statement, its status: fact, finding, estimate, opinion, proposal, question,
  decision, commitment;
- the caveats and unknowns that must survive;
- what the author is asking the reader for.

When rewriting existing text, the fact sheet comes from the source. Phrases like "plays a
crucial role" or "significantly improves" carry no fact; if a claim has no number or
concrete detail behind it, drop the adjective, keep the claim at the strength the source
supports, and flag it to the user if it matters.

### 3. Write

Decide between patching and rebuilding by what is actually wrong, not by who wrote the
source:

- **Rebuild** from the fact sheet when the role, relationship, or genre is wrong, the
  argument is in the wrong order, or structure-level tells run through the whole text
  (section scaffolding, bold-label bullets everywhere, wrap-ups, uniform rhythm). Don't
  paraphrase such a text sentence by sentence; that keeps its skeleton.
- **Patch** when the situation and structure are right and the tells are local phrases or
  words. Fix those spots and leave the rest alone.
- A text the user already accepted, or one that is direct and specific, gets patched or
  left unchanged, even if a model wrote it.

The scanner's `suggestion` line (step 4) is a hint for this decision. It never forces a
rebuild on its own.

Follow these rules. `references/patterns.md` has the full catalog with before/after
examples; `references/examples.md` has complete worked rewrites.

**Structure**

- Start with the point: the news, the number, the problem, or the ask. No purpose
  statement ("This document outlines..."), no background lap before the point.
- Use headings only when the text is long enough to need navigation (roughly 400+ words)
  or the template requires them. Sentence case, no emoji.
- Use a list only for items that really are parallel (steps, a set of options, several
  failures). Don't break an argument into bullets. Never start bullets with bold labels
  ("**Impact:** ...").
- Count things as they are. Two reasons are two. Don't pad to three, don't trim to three.
- No closing summary, "Overall", "Key takeaways", or moral at the end of a paragraph or
  document. End when the content ends, usually with the ask or the next concrete action.
- Let paragraphs differ in length and shape. Not every paragraph needs a topic sentence
  and a wrap-up sentence.
- In durable reference documentation, describe the current behavior, not the diff that
  introduced it: "Parameter X controls retries", not "We added Parameter X".
  Changelogs, release notes, migration guides, and PRs may describe changes.

**Sentences**

- Use plain verbs: is, are, has, was. "X is the main table", not "X serves as".
- Don't hang a significance comment on the end of a sentence (", ensuring...",
  ", highlighting the need for..."). If the consequence matters, state it as a fact in its
  own sentence.
- Don't frame a point against a claim nobody made: "not just X but Y", "this isn't about
  X, it's about Y", "Y rather than X" used as a rhythm. Say Y. One "rather than" where
  there is a real alternative is fine.
- No setup-reveal: "The result? ...", "Here's why: ...", "The bottom line: ...".
- No hedging disclaimers ("does not by itself establish", "based on the available
  information"). If something is uncertain, say concretely what is unknown: "We have no
  data for November yet."
- Mix sentence lengths the way the logic goes: a long sentence when two facts belong
  together, a short one for a decision. Avoid both the even 15-word drone and the newer
  staccato of 6-to-10-word declaratives.
- Lead with a material condition: "Yes, if X is enabled", not "Yes" followed by
  "but only if X is enabled" later. Keep the boundary as prominent as the answer.

**Words**

- Plain, specific words: use, help, check, fix, show, need, start, about, the table name,
  the job name, the number. "The nightly load failed 9 times in October", not
  "reliability challenges".
- Default-banned words and phrases are in `references/patterns.md` (delve, leverage,
  robust, seamless, pivotal, crucial role, foster, streamline, ensure that, it's worth
  noting, this matters, deep dive, circle back, and others). Rewrite the sentence; don't
  swap in a sibling synonym ("utilize" for "leverage" is the same smell).
- Repeat the exact term. Don't rotate synonyms for the same table, service, or metric.
- Praise and importance words need a number behind them or they go.

**Punctuation**

- No em dashes in English unless the author's own samples use them. Use a comma, colon,
  parentheses, or a new sentence.
- Don't overcorrect into commas and periods only. Parentheses, a colon before a list, an
  occasional semicolon are normal in human writing.
- Straight quotes in Markdown and chat. In Russian and Ukrainian the dash is ordinary
  punctuation and stays.

**Register for documents to a manager or leadership**

- Write as the person who did the work. "I" for what the author did or found, "we" only
  for things the team really did or agreed.
- Give bad news plainly with the cause: "The migration is two weeks late because the
  vendor API changed", not "We have encountered some challenges".
- Make the ask explicit and answerable: "Can I take this in the current sprint? The
  retention report would move to the next one."
- Don't ask the reader questions the author already knows the answer to, don't assign
  owners or deliverables unless the author has that authority and wants to, and don't add
  governance machinery (decision frameworks, RACI, timeboxed agendas) nobody asked for.
- No selling. A number beats "significant improvement".
- When asking the reader to choose or approve an option, compare the actual merits
  without loaded framing. "Already implemented", "current behavior", and "would
  require rework" belong in the explanation only when they are verified and relevant
  decision costs, not as a shortcut to favor the status quo. Don't hide real migration
  costs or imply options are equal when evidence says otherwise.
- Non-native English: plain and literal. No native idioms the author doesn't use
  ("nail down", "move the needle", "low-hanging fruit", "circle back").
- One "Thanks" is fine where the author would write it. No "I hope this finds you well",
  no "Let me know if you have any questions".

### 4. Scan

Save the draft to a file (and the source, if there is one) and run the scanner:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ai_tells.py" draft.md                      # pattern scan
python3 "${CLAUDE_SKILL_DIR}/scripts/ai_tells.py" draft.md --source original.md # plus token check
python3 "${CLAUDE_SKILL_DIR}/scripts/ai_tells.py" draft.md --lang ru            # force language
python3 "${CLAUDE_SKILL_DIR}/scripts/ai_tells.py" draft.md --allow "primary key" --allow-category em-dash
```

Claude Code replaces `${CLAUDE_SKILL_DIR}` with this skill's folder. In other hosts, use
the folder this SKILL.md was loaded from. For a short text with no file, pipe it in with
`-` as the path.

The output gives an advisory `suggestion` line, stats on sentence rhythm, each hit with
severity, line, excerpt, and reason, and (with `--source`) a token check. The scanner's
severities measure how strongly a pattern reads as AI, not how much harm it does; the
"Severity" section below decides priorities.

- Fix HIGH and MEDIUM hits by rewriting the sentence, not by swapping the flagged word.
- A hit is a legitimate exception when it is a term of art ("primary key", "critical
  path"), a quotation, a required template field, or the author's documented habit.
  Accept it explicitly: rerun with `--allow "PHRASE"` (or `--allow-category CATEGORY`
  for a whole habit, such as em dashes in an author who uses them) and keep a one-line
  note of why. Accepted exceptions then stop counting, so they can't trigger endless
  rework.
- LOW hits are prompts to look. Fix the ones that read as tells in context.
- Token check, `missing from draft`: must end up empty, or each item must be a deliberate,
  explained removal (for example, the user asked for a shorter version).
- Token check, `new in draft`: every new number, date, identifier, or URL needs support
  from the user or the conversation. If it has none, remove it.
- Token check, `negations` changed: re-read each negated claim against the source.
- The token check sees only presence. It can't tell that a claim was reversed or a
  limitation dropped; step 5 covers that.
- Run again after fixing. Stop when no HIGH hits remain, every remaining MEDIUM hit is
  fixed or accepted with a reason, and the token check is clean or explained.

If no shell is available, go through the checklist at the end of `references/patterns.md`
by hand, line by line, and tell the user the scan was manual.

### 5. Read it as the recipient

The scanner sees surface patterns only. Read the final text once more, start to finish,
as the actual reader:

- Would the author say each sentence out loud to this person without embarrassment?
- Is the first paragraph the thing the reader most needs?
- Could any paragraph be pasted into a different company's document unchanged? Then it
  says nothing; replace it with the specific fact or cut it.
- Does every adjective of importance have a number or a concrete detail behind it?
- Does the author sound like an insider who knows the system, or an outsider evaluating
  it?
- Are proposals still proposals and open questions still open? Did "we" grow into a team
  commitment nobody made?
- Do the sections all have the same shape (intro sentence, three bullets, wrap-up)?
- Is anything the user rejected earlier back under a different wording?
- Compare every claim with the fact sheet: same status, same certainty, same limits. A
  "does not show" in the source must not have become a positive finding.
- Does the text say that something was tested, checked, sent, migrated, or reviewed? Each
  such statement must match work the source or the user reports as done.
- Are options described without status-quo pressure, and are real implementation costs
  kept when relevant to the decision?
- Does a conditional answer state the condition up front? Is durable documentation
  describing current behavior rather than a historical diff?

If a check fails, fix the section, rescan, and read again.

### 6. Deliver

- **Draft or rewrite:** return the finished text, ready to paste. No preamble, no
  "Here's the revised version", no list of what changed. Keep chat and email text plain
  (no Markdown) unless the user asked for formatting.
- **Edit a file:** change it in place, re-read the saved file, and report the changes in
  two or three lines.
- After the text, add a short note only when the user must act on something: a fact that
  had to be dropped or could not be verified, a flag kept on purpose, an assumption about
  the reader. Don't claim the text is "now human" or "undetectable".
- Anything you say about your own work must match what you did: say "scanned" only if
  the scanner ran (otherwise "checked by hand"), "saved" only after the file was written
  and re-read, "all facts kept" only if the token check and the step 5 comparison passed.

## Severity

Rank findings by what they would do to the author if the text went out, not by how many
patterns matched. This scale is used in Detect output and when deciding what to fix first.

- **High:** a changed fact, number, or claim status; a limitation turned into a finding;
  an invented commitment, owner, date, or completed action; the author's position softened
  or reversed; the wrong role or relationship (insider written as consultant); a genre
  mismatch with real consequences; chatbot leakage or placeholders.
- **Medium:** structure-level AI patterns that make the text read as generated (section
  scaffolding, bold-label bullets, wrap-ups, uniform or staccato rhythm), a register that
  doesn't fit the reader, clusters of AI vocabulary or framing.
- **Low:** isolated words or punctuation, local polish.

One invented "we will deliver by Friday" outweighs any number of style hits. Never fix a
style hit in a way that creates a High finding.

## Detect mode

When asked to check a text (not rewrite it): do the step 1 situation check and the step 5
read, then run the scanner. Report findings grouped by the severity scale above, meaning
and role findings first, each with the excerpt, the reason, and a concrete fix. Name
meaning and role findings with these labels: Role or relationship mismatch, Authority
drift, Commitment drift, Unsupported completed-work claim, Artifact mismatch,
Shared-context mismatch, Stance drift, Limitation drift, Feedback regression. Pattern
findings use the scanner's category names. Mention the scanner suggestion only as
supporting evidence. If the text is clean, say so; don't invent findings.

When asked whether something was written by AI: report the patterns found and say plainly
that style alone can't prove authorship. Detector scores are unreliable (Wikipedia's own
guidance says they have non-trivial error rates and are thrown off by paraphrasing), so
don't optimize for them; the target is the human reader, and that is what this workflow
fixes.

## When the user says it still sounds wrong

Treat "this is not how I talk to my manager", "too corporate", or "still smells like AI"
as evidence that the situation or genre in step 1 was wrong, not as a request to tweak
wording or formatting. Rebuild the affected sections from the fact sheet, then check the
whole text for the same failure, not just the line the user pointed at. Keep every edit
the user accepted earlier. If the user names a phrase or structure they don't want, treat
it as a standing rule for the rest of the task.

## Don't overcorrect

- Formal vocabulary, perfect grammar, passive voice in a methods section, and transition
  words in isolation are not AI tells (Wikipedia lists them as ineffective indicators).
- A long design doc may need headings, tables, and numbered steps. Remove decoration, not
  structure the reader uses.
- Exact technical terms repeat. That is correct.
- Text that is already direct and specific gets few or no changes. "No changes needed" is
  a valid result.
- Don't replace one formula with another: a doc where every paragraph opens with a short
  punchy sentence is as mechanical as one where every paragraph ends with a summary.

## References

- `references/patterns.md`: the catalog of tells with fixes, and the manual checklist.
- `references/examples.md`: complete before/after rewrites (status update, Slack
  message, proposal, Russian status note).
- `references/context-cases.md`: role and genre failures (insider written as auditor,
  talking points turned into a facilitated agenda, proposals promoted into promises).
- `references/voice-profile.md`: template for the author's own writing samples.
- `scripts/ai_tells.py`: the advisory scanner and token check.
- `SOURCES.md`: where each rule comes from and which ones are design choices.
