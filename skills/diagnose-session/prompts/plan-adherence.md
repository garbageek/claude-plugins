Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Plan adherence

Recover the course of action the session agreed to, then map each step to what happened. A plan is any agreed course of action, not only a plan file.

1. Find the agreed plan: assistant text followed by human approval ("yes", "ok", "go ahead", or equivalent), a plan or spec file written or named during the session, task-list records whose meaning CASE established, or a numbered checklist in assistant text. Quote each step with its `path:line`.
2. Mark structural events between the plan and its execution: compactions, resumes, aborted turns, and subagent dispatches, using the meanings in CASE. Note their lines.
3. For each plan step, find the tool calls and assistant text that executed it, or establish that none did. Report:
   - steps skipped: no execution found; quote the step;
   - steps executed out of order: give the lines that show the order;
   - steps changed without notice: the execution differs from the step and the assistant never said so; quote both;
   - work no step covers;
   - drift immediately after a structural event: cite the event line and the first divergent action;
   - steps redone after a compaction although earlier lines show them complete.
4. If no plan is recoverable, report that as the only finding, with the lines you checked.
