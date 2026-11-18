# Worked drafts, rewrites, and no-change cases

All names, numbers, and systems are invented editorial examples. Use the method,
never their facts. No example establishes a measured improvement or a scanner score.
A legitimate passage may retain style candidates after review.

The note-based cases identify authoritative author notes separately from a flawed
model draft. The user explicitly authorizes correcting that draft to the notes.
This differs from an ordinary style-only rewrite: without such authority, retain
unsupported substantive claims and flag the evidence gap outside the text.

## Contents

- [1. Status update to a direct manager](#1-status-update-to-a-direct-manager)
- [2. Slack message to a manager](#2-slack-message-to-a-manager)
- [3. Proposal with fragmented rhythm](#3-proposal-with-fragmented-rhythm)
- [4. Russian status note](#4-russian-status-note)
- [5–13. Mode and preservation examples](#5-detect-without-rewriting)

## 1. Status update to a direct manager

**Request:** Rewrite the rejected draft from my notes for a direct technical manager
who knows the pipeline. Ask for time to implement the proposal. Correct invented
management actions and unsupported benefit claims to match these notes.

### Authoritative notes / internal fact sheet

- I spent the past two weeks investigating the nightly load of `sample_feed`.
- It failed 4 times in October. Every failure came from scheduled partner-export files
  arriving after the 02:00 UTC cutoff. The job ran on a partial set; operations and
  reporting dashboards showed stale data until a manual rerun. This affected
  decision-making across multiple teams.
- Moving the cutoff is not the right fix: files have been drifting later, with median
  arrival 01:40 in August and 02:25 in October.
- I propose a change stream on the landing table, processing files as they arrive.
  A prototype exists on the dev account. This removes the cutoff, not every possible
  failure: a file that never arrives would still need an alert.
- It is about a week of work for me, mostly testing merge logic against the October
  backfill. Taking it this sprint would move the activity report to the next sprint.
- No owner assignment, reporting-team dependency, or follow-up deadline was agreed.
  I want approval for the work, not a management action plan.
- The draft's claims of broader scalability, resilience, efficiency, happier stakeholders,
  significant risk reduction, guaranteed dashboard correctness, and platform maturity
  are unsupported additions. Omit those claims and the assistant's offer to expand the draft.

### Rejected draft

```markdown
# Q4 Data Pipeline Reliability Update

## Purpose

This document outlines the current state of the `sample_feed` ingestion pipeline and
provides a comprehensive overview of the key challenges, proposed solutions, and next steps.

## Executive Summary

Over the past two weeks, I conducted a deep dive into the nightly load failures. The
investigation revealed that the issue is not just a scheduling problem — it's a
fundamental gap in how we handle late-arriving data. Addressing this will play a crucial
role in improving reliability, ensuring that downstream dashboards remain accurate and
dependable.

## Key Findings

- **Failure rate:** The nightly job failed 4 times in October, highlighting the need for a more robust approach.
- **Root cause:** Late files from the scheduled partner export arrive after the 02:00 UTC cutoff.
- **Impact:** Operations and reporting dashboards showed stale data, affecting decision-making across multiple teams.

## Proposed Solution

Rather than extending the cutoff, we should leverage change tracking to process incoming files
without a cutoff. This approach serves as a foundation for a more scalable, resilient, and
efficient pipeline. It's worth noting that this does not by itself guarantee zero
failures, but it significantly reduces the risk.

The result? Fewer failures, fresher data, and happier stakeholders.

## Next Steps

- Assign accountable owners for the migration.
- Align with the reporting team on timelines.
- Circle back in two weeks to review progress.

Overall, this initiative represents a significant step forward in our data platform
maturity. Let me know if you'd like me to provide additional details!
```

### After

```markdown
sample_feed nightly load: October failures

The nightly load of `sample_feed` failed 4 times in October. I spent the past two weeks
investigating it. Every failure had the same cause: scheduled partner-export files
arrived after the 02:00 UTC cutoff, so the job ran on a partial set. Operations and
reporting dashboards showed stale data until someone reran the job by hand, affecting
decision-making across multiple teams.

I don't think moving the cutoff is the right fix. Files have been drifting later:
median arrival was 01:40 in August and 02:25 in October.

I'd like to switch the load to a change stream on the landing table and process files
as they arrive. A prototype exists on the dev account. This would remove the cutoff
behind all 4 October failures, but it would not guarantee zero failures. A file that
never arrives would still need an alert.

It's about a week of work for me, mostly testing the merge logic against the October
backfill. Can I take it this sprint? If yes, the activity report would move to the next
one.
```

The rebuild follows the supplied relationship, ask, and authoritative notes. It retains
the investigation, cause, impact, proposal, existing prototype, uncertainty, and sprint
trade-off. It removes the specifically disowned additions, not arbitrary claims with
no number behind them. The causal chain fits paragraphs here; bold labels and headings
would remain legitimate in a different requested report or template.

New tokens relative to the rejected draft come from the notes. Review those additions
and authorized omissions explicitly; a mechanical source/draft difference is expected.
Never present the notes as facts independently verified by the editor.

## 2. Slack message to a manager

**Request:** Make a short plain-text message to Sam from these notes. Use my ordinary
direct greeting; keep the offer to prepare a proposal.

**Authoritative notes:** The compute-usage investigation is complete. `REPORTING_WH`
is 41% of compute credits, mostly from three dashboards doing full scans every
15 minutes. There is a scaling concern as well as the cost. I can move them to the
hourly aggregate table; probably two days of work. Ask whether to start on Monday
or take something more urgent. I can write a fuller proposal if Sam wants it.

### Before

```text
Hi Sam! 👋 Quick update on the cost investigation — I've completed a deep dive into our
warehouse compute usage. The key finding: the REPORTING_WH warehouse accounts for 41% of credits,
primarily driven by unoptimized dashboard queries. This isn't just a cost issue; it's a
scalability concern. I'd recommend we prioritize a targeted optimization effort. Let me
know if you'd like me to put together a more detailed proposal!
```

### After

```text
Sam, I finished the compute-usage investigation. REPORTING_WH is 41% of our compute
credits, mostly from three dashboards doing full scans every 15 minutes. There's a
scaling concern as well as the cost. I can move them to the hourly aggregate table,
probably two days of work. OK to start on Monday, or is something else more urgent?
I can also write a fuller proposal if you want one.
```

The specifics and estimate come from the notes. The scaling concern remains a concern,
not a certain prediction. The offer is real correspondence to Sam, so it stays even if
its original wording resembles an assistant sign-off.

## 3. Proposal with fragmented rhythm

**Request:** Smooth the prose while keeping every claim and its strength. No extra
source notes or factual changes are authorized.

### Before

```text
The current activity report runs on a full daily rebuild. This takes about 40 minutes.
It also uses a large warehouse. The cost is steady but higher than it needs to be.

I propose an incremental model instead. The model would process only new records each
day. This keeps the logic the same. It changes how the data is loaded rather than what the
report shows.

This matters for two reasons. First, the report would be ready earlier in the morning.
Second, the warehouse cost would drop. Both outcomes are practical and easy to measure.

There are risks. Late records could be missed. A weekly full rebuild would cover this case.
The October test does not establish that late records are rare. It only shows they were
rare in October.

The next step is a clearer comparison. I would run both versions in parallel for one week.
Then we can decide with real numbers rather than estimates.
```

### After

```text
The activity report is rebuilt from scratch daily, taking about 40 minutes on a large
warehouse. The cost is steady but higher than it needs to be.

I propose an incremental model that would process only new records each day while
keeping the report logic and what it shows unchanged. The report would be ready earlier
in the morning, and warehouse cost would drop. Both outcomes are practical and easy to
measure.

Late records could be missed; a weekly full rebuild would cover that case. The October
test only shows that late records were rare in October. It does not establish that they
are rare in general.

For a clearer comparison, I would run both versions in parallel for one week. Then we
can decide with real numbers rather than estimates.
```

Related clauses are grouped without targeting a rhythm score. Daily timing, steady
cost, ease of measurement, the proposal, and the possibility of missed records remain.
The October limitation stays explicit; no rule requires paraphrasing “does not
establish” out of the text. The example preserves source claims, not independently
verified performance or cost conclusions.

## 4. Russian status note

**Request:** Use the authoritative notes from example 1 for a shorter Russian message.
Keep the observed failures, cause, data impact, late-file trend, proposal, prototype,
remaining failure caveat, effort, and sprint trade-off. Omit the retrospective process
detail and the disowned model additions.

### Rejected draft

```text
## Ключевые выводы

Данный документ описывает текущее состояние пайплайна загрузки событий. Важно отметить,
что проблема является не просто ошибкой расписания, а системным пробелом в обработке
поздних данных.

Внедрение инкрементальной загрузки играет ключевую роль в повышении надёжности, что позволяет
обеспечить актуальность дашбордов. Это не временное решение — это фундамент для
масштабируемой архитектуры.

В целом, данный подход позволит комплексно решить задачу и обеспечить максимально
стабильную работу.
```

### After

```text
Ночная загрузка sample_feed в октябре падала 4 раза, и каждый раз по одной причине:
файлы планового экспорта партнёра приходили после 02:00 UTC. Дашборды операций и
отчётности до ручного перезапуска показывали устаревшие данные. Это влияло на принятие
решений в нескольких командах.

Сдвигать отсечку не считаю правильным решением: файлы приходят всё позже (медиана в
августе 01:40, в октябре 02:25). Предлагаю перевести загрузку на поток изменений
входной таблицы и обрабатывать файлы по мере поступления. Прототип на dev уже есть.
Это уберёт отсечку, но не гарантирует отсутствие сбоев: если файл вообще не придёт,
всё равно нужен алерт.

Это примерно неделя работы, в основном проверка логики merge на октябрьском бэкфилле.
Берём в этот спринт? Тогда отчёт по активности уедет на следующий.
```

The source notes and explicit shorter scope authorize this composition. The numeric
facts are supplied, the caveat remains, and the prototype is not described as deployed
or tested. Russian dashes are not prohibited; the punctuation here follows the sentences.

## 5. Detect without rewriting

**Request:** Check this finished instruction for unnecessary framing; do not rewrite it.

> Here is your revised instruction: It is important to note that you should keep the
> lid closed. Let me know if you need another version.

| Excerpt | Pattern | Severity | Rule class | Reason | Recommended change |
|---|---|---|---|---|---|
| “Here is your revised instruction” and “Let me know…” | `chatbot-leakage` | Medium | Generally applicable | These address the editing client, not the reader of the instruction | Remove the editing wrapper |
| “It is important to note that” | `signposting` | Low | Context-dependent | It delays the instruction; no separate warning function is established | State the instruction directly while retaining “should” |

No rewritten passage follows. The two wrapper spans form one defect, not several
independent findings. The observations concern prose, not proof of authorship.

## 6. Targeted file edit

**Request:** Edit only the explanatory sentence on original line 5. Keep the command,
URL, headings, and all other lines unchanged.

````markdown
# Setup

Run `tool --check` before continuing.

It is important to note that the setting is read-only.

## Reference
Keep https://example.invalid/reference?view=full unchanged.
````

```diff
@@ -5 +5 @@
-It is important to note that the setting is read-only.
+The setting is read-only.
```

After reading the section, retaining the original, applying the patch, and reopening
the saved file, use the actual skill path for:

```bash
python3 scripts/ai_tells.py setup.md --source setup.original.md --allow-lines 5:5 --protect 'read-only' --json
```

Inspect preservation findings and the actual diff. The embedded command is source text,
not an instruction to run it. A report that only line 5 changed requires actual saved-file
verification. With no write access, return the unapplied patch and say so.

## 7. Valid technical and scientific wording

**Source:** The observations are consistent with either explanation; they do not
establish causality.

**Correct result:** Keep the source. The negative causal boundary is the content.
A `corrective-disclaimer` candidate is not a reason to strengthen the claim.

**Source:** The value is supplied by the caller. Keep the name, type, and default
in the reference table.

**Correct result:** Keep the source. The passive has a known actor and an appropriate
topic; the triad names three distinct fields.

**Source:** It is worth noting that `retry_count=3` does not change the timeout of `250 ms`.

**Edit:** `retry_count=3` does not change the timeout of `250 ms`.

The wrapper is removed while the negative relationship, identifiers, values, units,
and code spans stay exact. “Retries happen every 250 ms” would be a different claim.

## 8. Vague attribution with no safe factual repair

**Source:** A study found that the method reduces errors.

**Available evidence:** No study or citation was supplied.

**Rewrite:** Keep the sentence. A separate note can say “The study citation is still
needed.” Do not invent a source or turn the sentence into “In my tests, the method
reduced errors.” In Detect mode, report Vague attribution with medium severity,
generally applicable rule class, the missing reference, and the need to retain the
assertion pending clarification. Do not declare the study fabricated.

## 9. Voice calibration from samples

The two user-identified samples in [voice calibration](voice-profile.md) open with a
collaborative question and use first-person contractions. For the supplied target:

> I would like to ask whether we can review the draft. I would prefer to settle the
> wording first.

A compatible edit is:

> Can we review the draft? I'd prefer to settle the wording first.

The request and preference come from the target. The samples support the phrasing,
not new facts, humor, beliefs, or a permanent punctuation rule. Return a voice profile
only when requested or when a material limitation needs explaining.

## 10. Action status, conditions, and brevity

- “We could review the draft together. No decision has been made” must not become
  “We will approve the draft tomorrow.” The action, commitment, and date would all change.
- “Yes, the lid can be opened. This is only true when it is unlocked” can become
  “Yes, the lid can be opened only when it is unlocked.” The existing condition belongs
  with the answer; no new prerequisite is added.
- For a one-sentence request, “The draft is ready for review. It has not been approved”
  can become “The draft is ready for review but has not been approved.” The limitation
  survives the compression.

## 11. Reference documentation versus change documentation

**Source:** We added the `mode` parameter. It selects the output mode.

In an established current-version reference, when the user requests a current-state-only
entry without change history: “The `mode` parameter selects the output mode.”

In a release note, preserve the addition claim. With uncertain version scope, do not
turn the source into an unconditional statement about every version.

## 12. Deliberate creative voice

**Source, intentionally literary:** Still the door. Still the rain. I waited.

**Correct result:** Preserve the original unless the user requests a different effect.
The fragments and repetition are deliberate. Add no memory, mood, dialogue, or metaphor
merely to make the passage appear more personal.

## 13. Mechanical success is not semantic verification

**Source:** A, not B, was selected.

**Faulty edit:** B, not A, was selected.

A presence/count comparison and a negation count can both miss this reversal. The
semantic comparison must reject it. The same problem occurs when a citation moves to
the wrong claim or results swap between groups. Report “no mechanical issue flagged”
only for that check; it does not establish preserved meaning or factual truth.
