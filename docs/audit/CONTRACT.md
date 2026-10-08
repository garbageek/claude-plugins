# Audit Ticket Workflow Contract

This document defines the canonical behavioral contract shared by the audit-ticket skills, agents, CLI, hooks, and MCP server. All operational references must derive from this file instead of duplicating status tables or lifecycle rules.

---

## 1. Canonical Runtime Invocation

The structured `audit_*` MCP tools are the preferred machine interface in Claude
Code and local Codex. Pass the absolute target project directory as `root` on
every call. Initialize with `audit_init` only when ticket-lifecycle work is
requested; `deep-review` and `feature-scattering` remain read-only by default.

The canonical implementation is `scripts/audit.py` inside the installed plugin.
Do not assume an `audit` executable is on `PATH`, install a project-local copy,
or implement lifecycle transitions by editing Markdown.

### Resolve the installed plugin and the target project separately

Before a CLI fallback, determine the actual installed path from this loaded skill
or contract: the plugin directory contains `scripts/audit.py` and
`.claude-plugin/plugin.json`. Set `AUDIT_PLUGIN_ROOT` to that absolute directory
and `AUDIT_PROJECT_DIR` to the absolute project being audited. Reuse host-provided
paths only when they identify these same directories. Do not assume variables
set for hook/MCP processes also exist in an ordinary agent shell, and do not use
the plugin cache or the shell's incidental working directory as the project.

For a skill under `skills/<name>/SKILL.md`, the plugin root is two directories
above the skill directory. For a clone, it is the repository root containing `skills/` and `scripts/audit.py`.

```bash
export AUDIT_PLUGIN_ROOT="/absolute/installed/artur-plugins"
export AUDIT_PROJECT_DIR="/absolute/target/project"
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" <command>
```

Replace the example paths with observed paths. Include the assignments in the
same shell invocation when the host does not preserve environment variables
between calls. This is invocation setup, not a second runtime or an installed
wrapper.

### Host integration

- Claude uses `.mcp.json`, `hooks/hooks.json`, the shared skills, and `agents/`.
  Both host MCP configurations require an explicit absolute `root`; neither
  relies on the installed directory or a process working directory as a project.
- Codex uses `.codex-plugin/plugin.json`, which selects the same `skills/`,
  `mcp/codex.json`, and `hooks/codex.json`. This native manifest avoids the current
  portable AgentPlugin loader's hook-skipping branch. The absence of a root
  `plugin.json` is deliberate and checked by the repository validator.
- Init/status/next are shared skills, not duplicate platform command files.
  `audit-status` and `audit-next` remain read-only when no audit tree exists.
  `audit_init` and `audit_create` retain their explicit initialization behavior.
- `agents/*.md` are Claude role definitions. In Codex, delegate an independent
  verifier using the absolute verification skill path, target project, ticket IDs,
  fix revision, original acceptance criteria and available evidence. If fresh
  delegation is unavailable, hand off to a separate session/reviewer; a resolver
  cannot establish independence merely by changing role labels.
- Check actual hook discovery and trust in the installed host as described in
  [the operator guide](README.md#codex-hook-activation). When loaded, `PreToolUse`
  guards covered writes, `PostToolUse` diagnoses affected records, `SessionStart`
  reports existing audit state, and `Stop` emits an advisory health warning.

Role arguments enforce the transition matrix in the runtime; they are not
agent-identity authentication. Tool hooks are additional guardrails for covered
tool calls, not a filesystem sandbox. Do not claim that a skill enforces a
Claude model/tool allowlist in Codex or that hooks intercept every possible
external write.

Platform references: [OpenAI packaging](https://developers.openai.com/plugins/build/plugins),
[Codex hooks](https://learn.chatgpt.com/docs/hooks),
[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[portable MCP launch rules](https://agent-plugins.org/specification#stdio),
and [Claude hooks](https://code.claude.com/docs/en/hooks).

---

## 2. Canonical Status Enum

Persisted statuses:

```text
DRAFT                    # incomplete ticket; not eligible for resolution
OPEN                     # evidence-ready ticket accepted for resolution
READY_FOR_VERIFICATION   # fix implemented; independent verification pending
PASS                     # independently verified complete
PARTIAL                  # some criteria met; remaining work exists
FAIL                     # fix missing, incorrect, or insufficient
REGRESS                  # previously passing behavior broke again
BLOCKED                  # cannot proceed due dependency/access/context
WONTFIX                  # deliberate decision not to fix
INVALID                  # original ticket wrong, obsolete, or duplicate
```

Derived display-only state:

```text
UNVERIFIED               # no paired verification file exists; never persisted
```

---

## 3. Role Ownership

Every status-changing command must pass `--as <actor>`. Unknown or missing actors are rejected.

| Actor | May set statuses |
|-------|------------------|
| `audit-discovery` | `DRAFT`, `OPEN` |
| `audit-resolution` | `READY_FOR_VERIFICATION`, `BLOCKED`, `WONTFIX` |
| `audit-verification` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, `INVALID` |

Core rule: `audit-resolution` must never write `PASS`.

`audit-triage` is intentionally not a lifecycle actor. Triage commands may update scheduling and dependency metadata, but they must not gain lifecycle-status write permission by being added to the actor map for symmetry.

---

## 4. State Machine

A transition must satisfy both the current-state transition table and actor ownership.

| Current | Allowed next statuses |
|---------|------------------------|
| `DRAFT` | `OPEN`, `INVALID` |
| `OPEN` | `READY_FOR_VERIFICATION`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `READY_FOR_VERIFICATION` | `PASS`, `PARTIAL`, `FAIL`, `REGRESS`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `PARTIAL` | `READY_FOR_VERIFICATION`, `PASS`, `FAIL`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `FAIL` | `READY_FOR_VERIFICATION`, `WONTFIX`, `INVALID`, `BLOCKED` |
| `REGRESS` | `READY_FOR_VERIFICATION`, `PASS`, `PARTIAL`, `FAIL`, `BLOCKED`, `WONTFIX`, `INVALID` |
| `BLOCKED` | `OPEN`, `READY_FOR_VERIFICATION`, `PASS`, `PARTIAL`, `FAIL`, `WONTFIX`, `INVALID` |
| `PASS` | `REGRESS` |
| `WONTFIX` | `OPEN` |
| `INVALID` | `OPEN` |

The canonical runtime must expose this exact matrix. Changes to statuses, actors, transitions, or filename parsing are made once in `scripts/audit.py`; hooks and MCP invoke that runtime instead of maintaining mirrored lifecycle implementations.

---

## 5. Evidence Gates

### `DRAFT → OPEN`

`OPEN` requires real, non-placeholder content in:

- `## Description`
- `## Evidence`
- `## Acceptance Criteria`
- `## Suggested Verification`

Incomplete tickets stay `DRAFT` and are excluded from `audit_next(for_role="resolution")` or the CLI equivalent.

Placeholder content includes HTML comments, `TODO`, and brace placeholders such as `{description}` or `{path/to/file.py}`.

### `OPEN → READY_FOR_VERIFICATION`

Resolution requires:

- `--fix-commit`
- `--evidence`
- `--test`
- actor `audit-resolution`

Use:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" resolve 042 \
  --fix-commit abc123 \
  --evidence "Regression test added: tests/test_parser.py::test_null_input" \
  --test "pytest tests/test_parser.py: pass" \
  --changed src/parser.py \
  --as audit-resolution
```

### `READY_FOR_VERIFICATION → PASS`

`PASS` requires:

- actor `audit-verification`
- `--verified-commit`
- verdict text
- evidence/test record
- passing result for every acceptance criterion (`AC1`, `AC2`, ...)

Use:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" verify 042 \
  --status PASS \
  --verified-commit def456 \
  --criterion "AC1: pass - pytest tests/test_parser.py::test_null_input" \
  --evidence "Manual reproducer no longer fails" \
  --test "pytest tests/test_parser.py: pass" \
  --verdict "Fixed and covered" \
  --as audit-verification
```

---

## 6. Canonical Verification File Schema

```markdown
# Verification: NNN-CATEGORY-slug

**Original Ticket:** `audit/tickets/NNN-CATEGORY-slug.md`
**Original Category:** `CATEGORY`
**Original Severity:** `critical|high|medium|low`
**Verification Status:** `DRAFT|OPEN|READY_FOR_VERIFICATION|PASS|PARTIAL|FAIL|REGRESS|BLOCKED|WONTFIX|INVALID`
**Resolved Date:** `YYYY-MM-DD` or empty until resolved
**Resolved By:** `audit-resolution` or empty until resolved
**Verified Date:** `YYYY-MM-DD` or empty until independently verified
**Verified By:** `audit-verification` or empty until independently verified
**Fix Commit:** `sha` or empty until resolved
**Verified Commit:** `sha` or empty until independently verified

## Original Issue

## Resolution Evidence

## Criteria Results

## Verification Checklist

## Current State

## Evidence

## Test Verification

## Verdict
```

Backward compatibility: parsers may read legacy `**Status:**`, `**Date:**`, and `**Commit Verified At:**`, but new writes must use the canonical fields above.

Record metadata occupies the header before the first `##` section. Body evidence,
fenced examples and status history do not provide missing header values. Read and
update the first matching header field, preserving examples in the body. Empty
header fields must not consume the following line.

Covered `Edit`/`MultiEdit` and `apply_patch` operations compare the resulting
protected header fields. Evidence may quote a status without changing lifecycle
state. A patch to a managed record must have exact, unambiguous existing context;
unsupported/fuzzy/context-free patches are refused rather than guessed. Add
sufficient unchanged context or use the canonical runtime for lifecycle changes.


---

## 7. Canonical Ticket Metadata

Ticket files must use the filename format `{NNN}-{CATEGORY}-{slug}.md` and category enum:

```text
BUG
DEGRADED
LOST
TODO
TEST
CONFIG
SECURITY
CODE-QUALITY
```

Tickets also carry machine-readable fields:

```markdown
**Depends On:** `none` or `003, 007`
**Blocks:** `none` or `012`
**Impact:** `1-5`
**Effort:** `1-5`
**Priority:** `1-25`
**P-level:** `P0|P1|P2|P3`
**Decision:** `FIX|DEFER|WONTFIX|DUPLICATE`
**Phase:** `critical-path|quick-wins|feature-parity|backlog|...`
```

`audit_next(for_role="resolution")` or the CLI equivalent consumes this metadata plus dependency edges.

---

## 8. Dependency Semantics

Canonical edge meaning:

```text
003 blocks 001
```

Meaning: ticket `001` depends on ticket `003` and should not be selected for resolution until `003` is resolved.

Equivalent ticket field:

```markdown
**Depends On:** `003`
```

`audit_doctor` (or CLI `doctor`) rejects missing dependency targets, cycles, and dependencies that are unusable (`FAIL`, `BLOCKED`, `INVALID`).

The edge is recorded on both tickets: `Blocks` on the blocker and `Depends On` on the blocked ticket. Readers treat an edge recorded on only one side as a full edge. `audit_doctor` warns about such edges, and `audit_doctor(fix=true)` writes the missing side.

---

## 9. Git and Commit Ownership

| Action | Who may do it | Default |
|--------|---------------|---------|
| Implementation commit | `audit-resolution` | Project workflow dependent; never automatic from docs alone. |
| Verification metadata update | `audit-verification` | File write only by default. |
| Audit metadata commit | `audit` CLI | Opt-in via `--git-commit`; checks dirty worktree first. |

`--git-commit` fails on a dirty worktree unless `--allow-dirty` is explicitly passed.

---

## 10. Doctor Fix Semantics

`audit_doctor` (or CLI `doctor`) reports the current audit workflow health.

`audit_doctor(fix=true)` (or CLI `doctor --fix`) may create missing directories, onboarding files, or verification stubs, and may write the missing side of one-sided dependency edges. After applying any fix, the user-visible final result must be based on a fresh re-check, not on the pre-fix issue list.

A command may report both the fix attempt and the re-check, but the final issue count must represent the post-fix state.

---

## 11. Machine-Readable Output

When `--json` is passed:

- stdout contains JSON only;
- human output is suppressed;
- failed batch updates return non-zero exit status;
- batch JSON contains per-ID `updated` and `failed` arrays.

MCP tools must return structured JSON text in the MCP content envelope. If the wrapped CLI command emits human text, the MCP layer must normalize it into a JSON object and preserve the raw text in a named field such as `stdout_text`.

MCP `audit_create` has an explicit cold-start side effect: it initializes the audit tree before ticket creation. The tool result must expose both initialization and creation results, and must not continue to creation if initialization fails.

---

## 12. Reporting Source of Truth

The canonical source of truth is the normalized record produced by:

```bash
python3 "${AUDIT_PLUGIN_ROOT}/scripts/audit.py" --root "${AUDIT_PROJECT_DIR}" export --json
```

Reports and baselines should derive from this model rather than re-parsing different subsets independently. Baselines include status, semantic metadata, and content hashes.

`docs/audit/references/runtime-diagnosis-patterns.md` is a maintained operational reference and must be updated when runtime diagnosis behavior changes.
