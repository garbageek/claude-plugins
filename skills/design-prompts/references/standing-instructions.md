# Standing-instructions mode

Use through [design-prompts](../SKILL.md) when the target is text an agent loads on every run and obeys across many unrelated tasks: `AGENTS.md`, `CLAUDE.md`, a system prompt, a rules file. It covers two jobs: adding or repairing a rule after a failure, and consolidating a file that grew out of such patches.

This mode governs wording and structure only. For which file a host loads, its scope, precedence, and size budget, read [discovery and retention](../../../references/repo-instructions.md). For a read-only review of repository instructions against the code, use [review-repo-instructions](../../review-repo-instructions/SKILL.md). For the body of a skill, use [create-skill](../../create-skill/SKILL.md).

## What makes a rule work

A rule changes behavior only if the agent can tell, at the moment it acts, that the rule applies, what to do, and when it has done enough. Write every rule so that all three are answerable from the text.

- **Trigger.** Name the situation in terms the agent can observe: a kind of request, a state of the work, an event. "When a step is blocked" is observable; "when appropriate" is not.
- **Action.** Use an imperative the agent can carry out with the tools it has. Replace an intention or a quality adjective with the action that produces the quality.
- **Boundary.** State when the rule is satisfied, or where it stops applying. Put an exception next to its rule, not in another section.
- **Reason.** Add one clause of reason when it lets the agent decide cases the rule does not name. Omit it when the rule is a plain prohibition with no judgment involved.
- **Alternative.** When a prohibition leaves the agent without an obvious next move, say what to do instead.
- **One home.** State each behavior once, in the section that owns its topic. A second copy in other words reads as a second rule, and the differences between the copies become loopholes.
- **Closed lists.** Where the agent could pick a convenient reading (for example, acceptable reasons to stop), enumerate the allowed cases and say that nothing else qualifies.
- **Decision tables.** When the right response depends on the kind of request, use a table from request to response instead of scattered bullets.
- **Priority.** When two rules can collide, say which one wins. Do not rank by capitals, "critical", or repetition; if every rule is marked urgent, the marks carry no order.
- **No dead weight.** Delete words that cannot change an action: qualifiers true of every task in the file's scope, the story of the incident behind the rule, apologies, restated goals.

Deleting a scope qualifier (the file is loaded only inside the owner's projects, so the qualifier is true of every task):

```text
Before: Never add or write automated tests for the owner's projects.
After:  Never write automated tests.
```

Patching after a failure (the agent ended its turn with "Next I will deploy" although deployment had been requested):

```text
Weak:    Always make sure to fully complete tasks and never stop prematurely.
Working: Never end a turn with a statement of what you will do next.
         If the step is authorized and possible now, do it, then report.
```

The weak version names no observable situation and no action. The working version names the last message of a turn and the move to make.

## Add or repair a rule after a failure

1. Establish the failure from the conversation or transcript: the situation, what the agent did, what was expected. If the expected behavior cannot be determined, ask one question.
2. Read the whole target file and look for a rule that already covers the failure. If one exists, the failure shows that it was vague, contradicted, or outranked. Repair that rule in place. Never append a second rule that says the same thing.
3. If no rule covers it, write one at the level of the cause, so that it covers the class of situation without mentioning the incident. Do not widen it beyond what the user asked for; when you generalize past the incident, say so in the notes.
4. Put the rule in the section that owns the topic. Do not append it at the end, and do not create a section named after the incident.
5. Check the rule against the rest of the file: does it contradict, duplicate, or change the priority of an existing rule? Resolve what you find in the same edit.
6. Show the change as a diff or a before/after pair, and name the failure it addresses. Do not claim that it prevents the failure; that is untested until the agent runs with it.

Some failures cannot be fixed by text: a missing tool, a capability the host does not expose, a check that must be enforced by code. Say so instead of adding a rule that cannot be followed.

## Consolidate an accumulated file

Do this only when the user asks to rewrite, compress, or restructure the file. Otherwise use the minimal patch above.

1. **Inventory.** List every distinct behavior the file demands, merging repeats, and note where each appears. This ledger is a working artifact; deliver it only on request.
2. **Find collisions.** Mark rules that contradict each other or cover the same action differently. Resolve each one by the user's stated intent in the conversation. If that does not settle it and a wrong choice would be costly, ask; otherwise choose, and report the choice. Never resolve a contradiction silently.
3. **Decide per item:** keep, merge, sharpen, or drop. Drop only repeats, text with no behavioral effect, and qualifiers that are always true. Keep a rule whose purpose is unclear, and flag it in the notes.
4. **Restructure** around the decisions the agent faces, not around the history of incidents. Open with the context the rules depend on.
5. **Rewrite** each kept rule by the criteria in [What makes a rule work](#what-makes-a-rule-work). Keep identifiers, paths, commands, and enumerated values exactly as written.
6. **Check coverage.** Walk the ledger against the new file: every kept behavior appears once, and every dropped item has a stated reason. Do not introduce a behavior that was absent from the original unless the user asked for it.
7. **Deliver** the complete file in its native format when the target is a file; a fenced block is for prompts the user will paste. Add short notes outside the file: each contradiction and how it was resolved, what was dropped and why, and that the result has not been run against the agent unless it was.
