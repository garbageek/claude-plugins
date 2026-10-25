# Session diagnosis bundle

Session: <session-id>
Host: <name> <version> (<provenance label>)
Skill or plugin of interest: <name> <version> (<provenance label>), or "none"
Redaction level: skeleton | evidence | full
Built: <ISO timestamp>

## What this is

A scrubbed record of an agent session that went wrong, so that someone who was not present can check what happened. The report states what happened with `path:line` evidence. It contains no proposed fix.

## Files

- `report.md`: the diagnosis report.
- `case.md`: the case file the analysis used.
- `environment.json`: machine-readable environment section, with the provenance label and supporting location of each field.
- `timeline.md`: the per-turn timeline.
- `findings/<dimension>.md`: raw findings per dimension.
- `transcripts/<session-id>.md`: a condensed per-turn rendering of each examined session, never the raw JSONL. Original line numbers are kept as `[L<n>]` markers. Tool-result bodies by level:

  | Level    | Tool-result bodies                                                              |
  | -------- | ------------------------------------------------------------------------------- |
  | skeleton | Replaced by `[tool result: <tool>, <bytes> bytes, exit <code>]`                 |
  | evidence | Kept for cited events, including the commands and results that support findings |
  | full     | All kept                                                                        |
- `scrub-log.md`: every placeholder used, its category, and its count; never an original value.

## How to read it

Start with `report.md` sections 1 and 2, then section 6 and the evidence lines it cites, then the matching `[L<n>]` turns in `transcripts/`. `path:line` references point at the original files on the reporter's machine.

## Redaction

Placeholders look like `<EMAIL-1>`, `<PERSON-2>`, `<SECRET-3>`, `<HOST-4>`, `<REPO-5>`, `<ORG-6>`, `<PROPRIETARY-7>`; home paths become `~/...`. The same placeholder always refers to the same original value within this bundle. Scrubbing can miss things.

## Producer checklist

Replace this section with its results before showing the bundle.

1. Evidence support: for every exported finding, resolve its citation to an included `[L<n>]` marker, read the cited command, result, or quotation, and confirm it supports the claim. Path and line existence alone is not support. Record findings whose support the redaction level removed.
2. Consistency: reconcile report, case, environment, findings, and this README. Refresh scrub-log counts against the final files, excluding the log itself.
3. Outcomes, recorded separately:
   - Privacy audit: CLEAN, or the unresolved misses.
   - Evidence support: supported, or limited, with the affected findings and reasons.
4. If any file changes after a check, repeat the affected checks.
5. Show the final scrub log, file list, and both outcomes. Archive only after approval, then confirm the archive contains exactly the reviewed files. Record delivery outside the reviewed bundle.
