# Evidence and design rubric

Use this rubric to convert repository observations into Copilot Code Review guidance. The goal is not the largest number of checks; it is only those checks whose activation, mechanism, and evidence are strong enough to improve review precision.

## Contract ledger

Mandatory intermediate artifact. Keep one row per candidate repository-specific assertion in working notes (do not commit it unless asked). Each contract, source of truth, historical check, and intentional-pattern exception in the final files references one or more accepted rows. General finding and manual-verification gates are not project assertions and need no rows.

| Field             | Required question                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| ID                | Short stable identifier, for example `C3` or `H1` (historical)                                                           |
| Activation        | Which changed path, hunk, API, data flow, configuration, or behavior makes this check relevant?                          |
| Contract          | What externally meaningful or architecturally established behavior has to stay true?                                     |
| Evidence          | Which file, schema, validator, workflow, deployment file, policy, or history item establishes it? `path@sha` or PR #     |
| Evidence role     | Normative (defines the obligation) or behavioral (shows current execution)? See source roles                             |
| Strength          | Enforced (CI, validator, runtime check), normative document, implementation-near, confirmed history, or suggestive?      |
| Durability        | Could a valid redesign change today's implementation while this behavior stays valid? If yes, state the behavior instead |
| Failure mechanism | What exact execution, data, compatibility, packaging, or deployment path fails when the changed hunk violates it?        |
| Impact            | What observable runtime, persisted-data, API, packaging, deployment, architectural, or documented behavior breaks?       |
| Reviewability     | Can static review establish it (call path, types, guards, semantics), or does it need runtime, UI, or external data?     |
| Destination       | Skill, path-specific file, existing owner file, review environment, MCP, or nowhere                                      |
| Decision          | Accept, narrow, manual verification, or reject, with a one-line reason                                                   |

Reject a row if activation, evidence, failure mechanism, or impact is missing. Suggestive evidence alone never produces a check. Move a row to manual verification only if it passes the manual-verification gate below; otherwise reject it.

## Source roles

Two different questions, two kinds of evidence:

- **What happens now (behavioral):** runtime implementation, validators, migrations, persistence code, build, packaging, deployment, and CI automation. Nearest-to-behavior evidence wins.
- **What has to stay true (normative):** public schemas and API contracts, compatibility or deprecation policies, maintained contract documentation, recorded decisions (ADRs, maintainer statements), and enforced checks.

An enforced check is both. Implementation alone can itself violate the contract, so it does not by itself make current behavior an obligation. README prose and code comments are supporting context only.

Not repository contracts by themselves: framework convention, ecosystem best practice, current file layout, an isolated review comment, an abandoned PR, a generated artifact whose generator is the canonical owner, text in an existing agent instruction file that the code contradicts, and any absence (of tests, validation, documentation, or incidents). Absence of evidence proves neither presence nor absence of a contract.

## Conflicting sources

When sources disagree (for example README, runtime code, and deployment script):

1. State the disagreement explicitly in the ledger.
2. Determine whether one source is stale (history, last-modified, who consumes it).
3. Inspect every runtime, build, packaging, and deployment path that actually consumes the behavior.
4. Check whether documented compatibility semantics intentionally differ from the implementation, and whether the implementation is the defect.
5. Encode a rule only once the contract is established; otherwise record the conflict in the final report and encode nothing.

A file is not authoritative because its name looks canonical.

## Durable contract test

Ask: could the project be correctly redesigned so that this implementation detail changes while user-visible, compatibility, deployment, and documented behavior stays valid? If yes, encode the behavior, not the detail.

- Prefer: "persisted identifiers remain readable across upgrades".
- Over: "this helper parses identifiers".

## Remedy-freezing test

A fix shows that the removed thing was a defect. It does not show that the replacement it chose is required. Before encoding anything learned from a fix, split it:

- **Defect class (encode):** what was wrong and why it breaks something. Example: committed environment-specific resource IDs in deployable configuration.
- **Chosen remedy (do not encode):** the specific names, values, destinations, helpers, or libraries the fix happened to use. Example: requiring lookups by two particular destination names.

Encode the remedy only when a normative source (policy, schema, enforced check) independently requires it. A valid future rename or reroute that keeps the invariant must not trigger a finding.

## Temporal wording test

Review guidance is long-lived; a phase-bound statement becomes a false rule when the phase ends. Remove or rewrite wording such as "after cutover", "currently", "for now", "during the migration", "until X ships", "new" or "old" system, unless the repository encodes that phase with an explicit end condition (a flag, a dated deprecation, a tracked removal). If the rule matters only during the phase, it belongs in the PR or issue for that work, not in review guidance.

## Session-salience test

What the agent worked on recently distorts two things: how much weight a piece of evidence gets, and which topics get rules at all. Guard both.

**Evidence weight.** The current session, a PR you just helped with, or a review comment you drafted is not a source by itself. It enters the ledger only through its repository artifact (commit, merged PR, issue) and then has the standing of one incident, subject to the historical regression and remedy-freezing tests.

**Topic selection.** Candidates come from a domain-by-domain sweep of the repository, not from what is fresh in context. Before sweeping, write down the topics the session already touched. After the ledger is drafted:

1. Mark every row whose topic overlaps a session topic.
2. A marked row survives only with evidence independent of the session work: a normative source that requires it, an enforced check, or the same pattern established across the repository (not only in the files the session changed).
3. Apply the cold-start test to every row: could the rule be justified to an agent starting from the default branch with no knowledge of this session, using only cited repository evidence? The session may be how you found the evidence; it cannot be the evidence. If no such citation exists, reject the row.
4. Check balance: if accepted rules cluster on session topics while other domains from the sweep have none, the sweep is incomplete; revisit the uncovered domains before delivery. Balance is not a quota: a domain with no evidence gets no rule.

**Session knowledge proposes, repository evidence decides.** Deep prior work on a repository is a valuable source of candidates: an agent that has been through the code many times may know a fragile path or a real invariant that a fresh sweep misses. Keep those candidates; just hold them to the same bar. For each session-derived row, locate the evidence in the repository and cite it as if you had found it cold. If you can cite it, the rule stands on that citation, not on the session. If you cannot, reject it, however confident the session makes you feel.

**Two-pass option.** When the session holds substantial prior work and a fresh-context agent is available, combine both:

1. The fresh agent builds a candidate list from the repository alone (the baseline).
2. The session-aware agent adds candidates the baseline missed.
3. Rules in both lists are strong. Rules only in the baseline are kept on their evidence. Rules only from the session-aware agent are the valuable extra and the main risk: each needs a cold citation and passes the remedy-freezing and temporal-wording tests, or it is dropped.

## Review-history classification

| Label                   | Criteria                                                                                                                   | Use                                                                 |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Confirmed defect        | Mechanism established by current code semantics or maintainer confirmation; holds even if never fixed                      | Evidence for a contract or a known-risk area                        |
| Confirmed fix           | Chain holds: original diff -> finding -> specific fix -> same mechanism eliminated                                         | Corroborates the defect; required for a historical regression check |
| Speculative             | Activation, call path, causality, or impact assumed                                                                        | Target for the finding gate or an intentional-pattern entry         |
| Coverage-only           | Asks for tests or coverage without naming a current defect                                                                 | Covered by the general exclusion; no new rule                       |
| Generic recommendation  | Style, maintainability, or best-practice advice with no project-specific breakage                                          | Evidence that a surface injects generic filler                      |
| Mislabeled verification | Concrete uncertainty needing runtime, UI, environment, or external data, presented as a defect                             | Target for the manual-verification gate                             |
| Intentional pattern hit | Flags a pattern the repository uses on purpose, confirmed by code, normative docs, or maintainer reply                     | Target for an evidenced intentional-pattern entry                   |
| Repeat                  | Same comment repeated on re-review                                                                                         | Not independent evidence; count once                                |
| Unresolved              | No established mechanism, no reply, abandoned PR, or a later commit touching nearby code without fixing the same mechanism | Not evidence either way                                             |

Prefer merged default-branch evidence and maintainer-confirmed resolutions over open or abandoned discussions.

## Historical regression test

Before turning history into a check, establish:

1. the historical failure mechanism;
2. the code or configuration path that enabled it;
3. the observable impact;
4. the corrective change, used only to confirm the mechanism was removed (see remedy-freezing test);
5. the current diff condition that could reintroduce it.

If step 5 is absent, the incident is context, not an active check. One confirmed incident supports a narrowly triggered check; "recurring" requires several confirmed cases with the same mechanism. Phrase checks as: "when a change does X, verify Y still preserves Z; regression R occurred when mechanism M bypassed it". Z is the invariant, never the specific remedy the fix used. Never generalize into "watch performance", "be careful with caching", "check migrations", or "avoid expensive queries".

## Finding gate (for the generated guidance)

Every defect claim, at any severity:

`activation -> changed hunk -> reachable scenario -> failure mechanism -> observable impact -> evidence`

- A true repository rule that the diff cannot violate produces no finding.
- Static proof is enough: call paths, types, guards, control flow, and language semantics. No runtime run, past incident, or written rule is required.
- Before reporting, check callers, guards, fallbacks, and handlers that could refute the defect.
- Low severity does not compensate for a missing link. Severity is chosen after the defect is established.
- Not defects by themselves: missing tests, PR size, complexity, production exposure, a database or shared state, inability to run the app, UI, or an environment, and theoretical risk without a demonstrated call path.

## Manual-verification gate

An item is allowed only when all hold:

- the diff creates a specific unresolved question;
- the question materially affects changed behavior;
- repository evidence cannot resolve it statically.

Each item states the exact action, the condition, and the expected result. It is not a defect. Broad items ("test this manually", "verify the UI", "check production") are not allowed. If the basis is missing, delete the item; do not trade speculative defects for speculative checklists.

## Mechanism placement

| Knowledge                                                                           | Home                                                                            |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Review-only contracts, regression checks, finding gates                             | `.github/skills/code-review/SKILL.md` plus sibling detail files                 |
| Review-only rules that must load for a distinct path domain                         | `.github/instructions/<name>.instructions.md`, `excludeAgent: "cloud-agent"`    |
| Coding guidance in a path-specific file that is noise in review                     | Add `excludeAgent: "code-review"` to that `*.instructions.md` file              |
| Coding guidance in `copilot-instructions.md` or `AGENTS.md` that is noise in review | Narrow it in its owner, or move it to a path-specific file excluded from review |
| Guidance for coding and review alike                                                | Existing owner: `copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`             |
| Contract checkable only by running a repository tool                                | Review environment workflow, with explicit user approval                        |
| External facts or runtime state not in the repository                               | MCP in repository settings (recommend, do not configure)                        |
| Nothing accepted, or existing surfaces already sufficient                           | No change; report why                                                           |

Never copy a rule into two surfaces to raise the odds Copilot sees it; duplication adds conflict risk and consumes context. Refine the existing owner instead.

## Final red-team pass

Challenge every rule in the finished files:

- For contracts and historical checks: is there a precise activation condition, or could it fire on unrelated diffs?
- Could a valid redesign violate the wording without breaking anything?
- Does it freeze a remedy from one fix (specific names, values, destinations, helpers) instead of the defect class?
- Does it contain phase-bound wording ("after cutover", "for now", "during the migration") without a repository-encoded end condition?
- Does its only evidence come from the current session or a PR you just worked on?
- Would an agent starting cold from the default branch reach this rule, and do accepted rules cluster on session topics while other domains are uncovered?
- Is the evidence current at the branch head, and normative where the wording is strong?
- Were all build, packaging, and deployment paths checked?
- Does history establish the same mechanism, not just a nearby edit?
- Is the check tied to changed code rather than untouched legacy code?
- Can static review actually establish the claimed failure?
- Would the wording turn uncertainty into a defect, or into a manual-verification item that fails the gate?
- Could the wording suppress a statically provable defect?
- Could no finding be the correct result?
- Does the wording claim more strength (`must`, `never`, `source of truth`) than the evidence has?
- Does another surface already own this rule, or does it contradict one?
- Does it rely on an unsupported instruction type (comment format, overview, merge blocking), or depend on following an external link to be understood?
- Does it use a private meaning of "blocking" instead of confirmed defect plus severity by impact?

Delete, narrow, or downgrade any rule that fails.
