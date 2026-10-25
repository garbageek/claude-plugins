Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Stumbles

Find every point where the session stopped moving forward. Use the record meanings and extraction commands in CASE to locate line numbers for:

- tool results marked as errors, non-zero exits, or explicit failure records;
- failed shell commands (non-zero exit, "command not found", "No such file");
- retries: the same tool call issued again in the same turn after an error;
- reverted edits: an edit followed by one restoring the earlier content, or `git checkout`, `git restore`, `git revert`, or `git reset` on a file the session touched;
- backtracking in assistant text ("actually", "let me instead", "that was wrong", "I misread");
- human corrections: a human prompt contradicting or correcting the assistant's preceding action;
- permission denials, hook failures, API errors, rate limits, aborted turns, context overflow, and compaction in the middle of a task.

For each, report the line, the turn, what failed, and what happened next: recovered in the same turn, recovered later at line N, or never recovered. Group identical repeated failures into one finding with a count.
