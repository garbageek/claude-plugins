Read `prompts/analyst-common.md` first; it defines your role, inputs, context safety, and return format. This file adds the dimension.

Dimension: Quality evidence

Judge the process against its own claims. This is not a code review; do not evaluate the code the session produced.

1. Claims: find assistant text claiming done, fixed, passing, verified, works, or complete. For each, look back within the same turn for a tool result that shows it: a command and its output, a diff, a read-back of the written file. Report claims with no supporting result in that turn, and claims contradicted by an earlier result.
2. Checks run: every build, lint, check, or test command the session ran, with its result line. Report failed runs and what the assistant did next, including runs whose failure was not mentioned.
3. Delegated work: where a subagent reported success, report whether the controller inspected the resulting changes or relied on the report alone.
4. Commits and published text: every `git commit`, push, PR, or comment, with its message. Report messages that claim work no tool call performed.
5. Review feedback: where a human or subagent reviewer raised points, find the response. Report points acknowledged but not acted on, and points dismissed without a stated reason.
6. Acceptance criteria: when the problem statement or the agreed plan states criteria, report each as met, not met, or not checked, with the evidence line.
