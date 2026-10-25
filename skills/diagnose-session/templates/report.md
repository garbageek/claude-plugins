# Session diagnosis: <session-id>

Report path: <absolute workspace path>/report.md
Written: <ISO timestamp>

## 1. Problem statement

<Copied from the case file, including whether it was agreed or the broadest reading.>

## 2. Verdict

<What the evidence shows happened around the reported problem. Prose, with `path:line` after every claim. State confidence (high, medium, low) and the observation that would raise it. No proposed change.>

## 3. Environment

<From the case file, with the provenance label and supporting location of every field.>

## 4. Sessions examined

| Role | Session id | Absolute path | Lines | Bytes |
| ---- | ---------- | ------------- | ----- | ----- |

Rejected candidates: <id, path, why>, or "none".

## 5. Timeline

One row per human prompt. Events lists skills invoked, subagents dispatched, compactions, errors, resumes, and aborts.

| Turn | Line | Time | Request (one line) | Events |
| ---- | ---- | ---- | ------------------ | ------ |

## 6. Findings

Each finding:

```text
- finding: <one sentence>
  evidence: <path>:<line> - "<short quote>"
  turns: <first>-<last>
  confidence: high | medium | low
```

A dimension with nothing to report says `none found - checked: <what>`. A dimension not run says `not run - <reason>`.

### 6.1 Skill timeline
### 6.2 Plan adherence
### 6.3 Repeated work
### 6.4 Stumbles
### 6.5 Quality evidence
### 6.6 Request conflicts
### 6.7 Cost and time

## 7. Involvement of the skill or plugin of interest

<Only when the case names one.> not indicated | possible | likely

Evidence lines: <path:line list>. This section states involvement only. It does not name a defect or propose a change; a requested change is separate work that uses this report as evidence.

## 8. Coverage notes

- Not read: <ranges and files, and why>
- Dimensions not run: <list and reason>, or "none"
- Host features or records unavailable: <list>, or "none"
- Session in progress at read time: yes | no
- For the user to double-check: <list>, or "none"

## 9. Similar sessions (only when requested)

| Session id | Path | Date | Host | Matched | Did not match |
| ---------- | ---- | ---- | ---- | ------- | ------------- |
