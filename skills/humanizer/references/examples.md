# Worked rewrites

All names, numbers, and systems here are invented sample data. Use the method, never the
facts. Each "after" text passes `scripts/ai_tells.py` with no HIGH or MEDIUM hits.

In these examples the "before" is a model draft written from the author's notes, and the
"after" is rewritten from the same notes. Facts that appear only in the "after" are marked
as coming from the notes. In real use, anything the source and the user don't supply stays
out; the token check lists new numbers and identifiers so you can confirm each one.

## 1. Status update to a direct manager

The manager knows the pipeline. The engineer wants approval to spend a sprint on a fix.

### Before (typical model output)

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

Scanner: 1 HIGH, 19 MEDIUM; suggestion "rebuild-candidate" (formatting-overuse,
inline-header-list, purpose-statement, rule-of-three, uniform-rhythm, wrap-up). The
decision to rebuild comes from the situation check: a status note to a manager who knows
the system, written as a formal report with invented management actions.

### Fact sheet (internal)

- Finding: `sample_feed` nightly load failed 4 times in October.
- Finding: cause in all cases: scheduled export files arrive after 02:00 UTC cutoff.
- Finding: operations and reporting dashboards showed stale data.
- Opinion: extending the cutoff is not the right fix.
- Proposal: switch to incremental change tracking, process incrementally.
- Caveat: streams don't guarantee zero failures.
- From the author's notes (not in the draft): the job runs on a partial set and someone
  reruns it by hand; late files drift later, median 01:40 in August and 02:25 in October;
  a prototype stream on the landing table exists on the dev account; a file that never
  arrives would still need an alert; about a week of work, mostly testing the merge logic
  against the October backfill; the activity report would slip a sprint.
- Ask: time to do it. The author confirmed that "assign owners" and "align with reporting"
  were not his intent: he has no authority to assign owners and there is no cross-team
  dependency. Dropped.

### After

```text
sample_feed nightly load: October failures

The nightly load of sample_feed failed 4 times in October. Every time the cause was the
same: export files from the source system arrived after the 02:00 UTC cutoff, the job
ran on a partial set, and the dashboards used by operations and reporting showed the previous day's
numbers until someone reran it by hand.

Moving the cutoff later would hide the problem for a while, but the late files have been
drifting later since August (median arrival was 01:40 in August, 02:25 in October), so I
don't think it buys us much.

What I'd like to do instead is switch the load to a change stream on the landing table
and process files as they arrive. I have a working prototype on the dev account. It won't
remove every failure (if a file never arrives we still need an alert), but it removes the
cutoff, which is where all 4 October failures came from.

It's about a week of work for me, mostly testing the merge logic against the October
backfill. Can I take it this sprint? If yes, the activity report would slip to the next
one.
```

What changed and why:

- The news (4 failures, one cause) moved to the first sentence. Purpose section, summary,
  and wrap-up are gone.
- Bold-label bullets became two sentences, because the three "findings" are one causal
  chain, not a list.
- "Crucial role", "robust", "scalable, resilient, and efficient", "happier stakeholders"
  had no facts behind them. The fact that replaced them: all 4 failures came from the
  cutoff the proposal removes.
- "Does not by itself guarantee zero failures" became the concrete gap from the notes: a
  missing file still needs an alert. The limitation keeps its strength.
- The invented management actions are gone. The ask is the engineer's real ask: time.

## 2. Slack message to a manager

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
Sam, REPORTING_WH is 41% of our compute credits. Most of it is three dashboards that
run full scans every 15 minutes. Besides the cost, it will become a scaling problem. I can
move them to the hourly aggregate table, probably two days of work. OK to start on Monday,
or is there something with higher priority? I can also write up a more detailed proposal
if you want one.
```

Notes: the three dashboards, the 15-minute schedule, the hourly table, the two-day
estimate, and Monday come from the author's notes; the model version hid them behind
"unoptimized dashboard queries" and "a targeted optimization effort". The scaling concern
and the offer of a detailed proposal are the author's points, so both stay, in plain
words.

## 3. Proposal in 2026 staccato style

Newer models avoid em dashes and the classic vocabulary but write chains of short
declaratives with "This matters", "rather than", "does not establish", and words like
steady, practical, clearer.

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

Scanner: suggestion "rebuild-candidate" (staccato, uniform-rhythm), plus a 2026
vocabulary cluster, two "rather than", "This matters", and a corrective disclaimer. The
structure itself is the problem here: every thought is cut into separate short sentences.

### After

```text
The activity report is rebuilt from scratch every night. It takes about 40 minutes on a
large warehouse and costs more than it needs to. If we loaded only the new records each
day, the report logic and what it shows would stay the same, the report would be ready
earlier in the morning, and the warehouse cost would drop.

The risk is late records: a record that arrives after its day was processed would be
missed. A full rebuild once a week would pick those up. The October test showed late
records were rare that month, which doesn't tell us whether they are rare in general.

I'd like to run both versions side by side for a week and decide with real numbers.
```

## 4. Russian status note

### Before

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
Ночная загрузка sample_feed в октябре падала 4 раза, и каждый раз по одной причине: файлы
источника приходили после 02:00 UTC. Отчёты по операциям и аналитике до ручного перезапуска
показывали вчерашние цифры.

Сдвигать отсечку не хочу: файлы приходят всё позже (медиана в августе 01:40, в октябре
02:25). Предлагаю перевести загрузку на поток изменений, прототип на dev уже есть. Это
примерно неделя работы. Берём в этот спринт? Тогда отчёт по активности уедет на следующий.
```

Notes: as in example 1, the numbers, times, and the sprint trade-off come from the
author's notes, which the model draft had replaced with general statements. The dash
after «отсечку не хочу» would be fine in Russian; a colon was simply the better fit here.
