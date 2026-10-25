# Case: <session-id>

Workspace: <absolute workspace path>
Created: <ISO timestamp>

## Problem statement

<One paragraph: the session(s), the turn range if known, what was expected, what happened, and the observable that matters (wall-clock time, tokens, a repeated action, a specific action, a skill that did or did not run). Mark it "agreed with the user" or "broadest reading, user unavailable".>

Skill or plugin of interest: <name and install root, or "none">
Requested outputs: report | similar sessions | evidence bundle | issue draft

## Sessions

| Role     | Session id | Absolute path | Compressed | Lines | Bytes | Longest line (bytes) | First human prompt (first 120 chars) | First timestamp |
| -------- | ---------- | ------------- | ---------- | ----- | ----- | -------------------- | ------------------------------------ | --------------- |
| main     |            |               |            |       |       |                      |                                      |                 |
| subagent |            |               |            |       |       |                      |                                      |                 |

Rejected candidates: <id, path, why rejected>, or "none".

Session still running at read time: yes | no (mtime <ISO>, lines <N>)

## Environment

Label every field `historical evidence`, `unverified snapshot`, `current observation`, or `unknown`, and give its supporting location. Current versions and file times do not establish what was installed during the session; one captured skill body does not authenticate a whole installation.

- OS:
- Host and version:
- Models seen: <model id, where (main or subagent id)>
- Skills, plugins, MCP servers, and hooks evidenced in the session:

| Name | Kind | Source path or install root | Version or hash | Provenance | Supporting location |
| ---- | ---- | --------------------------- | --------------- | ---------- | ------------------- |

- Instruction files loaded (paths only):

## Context-safety rules for every reader

- Follow `<absolute path to references/context-safety.md>` before reading any file listed here.
- In a subagent transcript, "user" is the parent agent.

## Discovered sources and record meanings

- Sources consulted: <absolute paths, tools, help output, documentation>
- Extraction commands: <bounded commands for each source, including the stream command for compressed files>
- Identity evidence: <session id, working directory, timestamps, matching content, line numbers>
- Associated sessions: <id, relationship, supporting lines>, or "none found"
- Human messages: <record shape and the evidence for that meaning>
- Injected context and parent dispatches: <record shape and evidence>
- Assistant messages: <record shape and evidence>
- Tool calls and results: <record shapes, how they are matched, evidence>
- Skill invocations: <record shape and evidence>, or "unavailable"
- Usage counters: <fields; per-message, per-turn, or cumulative; units; evidence>, or "unavailable"
- Timing: <fields, units, event boundaries, evidence>, or "unavailable"
- Compaction, resume, and fork records: <record shape and evidence>, or "none found"
- Unresolved information: <missing, inaccessible, or ambiguous items>, or "none"
