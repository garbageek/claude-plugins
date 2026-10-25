Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Cost and time

Account for where tokens and wall-clock time went. Use only the counters, timestamps, and meanings recorded in CASE.

1. Tokens: state whether each counter is per-message, per-turn, or cumulative before adding anything. Difference cumulative counters; never treat a missing observation as zero. Report the five turns with the largest supported totals and the supported total per associated session. Do not convert tokens to money unless CASE records a price source the user supplied.
2. Wall-clock: report the five longest supported turns and every gap over ten minutes between consecutive events. Say whether a gap was idle, waiting on a subagent, or waiting on the user only when the records show it.
3. Largest tool results: report the ten largest tool results with their tool and turn, measuring records before extracting any content. Include spilled tool-result files when CASE lists them.
4. Compactions: count and locate them. Report the counters available before and after each and what the session was doing when it fired; mark unsupported fields as absent.
5. Associated sessions: count them and report supported usage, duration, and the dispatching turn of each.
6. Report the turns, subagents, tools, or repetitions that dominate the totals, with numbers. Do not speculate about why a turn was expensive beyond what the transcript shows.
