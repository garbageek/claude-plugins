# Verification Detail Template

Reference schema only. Create/update verification records through the CLI; never overwrite an existing record or its history with this template.

````markdown
# Verification: {ticket-id}

**Original Ticket:** `audit/tickets/{ticket-id}.md`
**Original Category:** `BUG`
**Original Severity:** `critical`
**Verification Status:** `READY_FOR_VERIFICATION`
**Resolved Date:** {YYYY-MM-DD or empty}
**Resolved By:** `audit-resolution` or empty
**Verified Date:** {YYYY-MM-DD or empty until independently verified}
**Verified By:** `audit-verification` or empty until independently verified
**Fix Commit:** {implementation sha or empty}
**Verified Commit:** {sha checked by verifier or empty}

## Original Issue

{Brief summary of what the ticket reported — copy from original ticket.}

## Resolution Evidence

{Evidence supplied by audit-resolution: changed files, tests, reproducer result, known caveats.}

## Criteria Results

- [ ] AC1: {pass|fail|partial} — {evidence command/file/output}
- [ ] AC2: {pass|fail|partial} — {evidence command/file/output}

## Verification Checklist

{Use category-specific checklist below.}

## Current State

{Description of what exists now in the codebase.}

**File(s) Changed:**
- `{path/to/file.py}` lines {N-M}

## Evidence

{Code snippets, test output, screenshots, or reproduction results proving the verdict.}

## Test Verification

```bash
# Command run
{test command}

# Result
{output}
```

## Notes

{Any caveats, follow-up items, or context.}

## Verdict

**{PASS|PARTIAL|FAIL|REGRESS|WONTFIX|BLOCKED|INVALID}**

{One-line justification.}

## Verification History

{The runtime archives previous proof here when a cycle or checked revision changes.}
````

## CLI Verification Commands

PASS requires the latest result for every acceptance criterion to be `pass` in
the current cycle and checked revision. Previous cycles and revisions are retained
under `## Verification History`; their evidence does not satisfy PASS. Reuse
partial results only on the same recorded Verified Commit.

```bash
python3 "/path/to/audit-workflow/scripts/audit.py" --root "/path/to/project" verify 001 \
  --status PASS \
  --verified-commit def456 \
  --criterion "AC1: pass - pytest tests/test_x.py::test_case" \
  --criterion "AC2: pass - manual reproducer no longer fails" \
  --evidence "Reproducer no longer fails" \
  --test "pytest tests/test_x.py: pass" \
  --verdict "Fixed and covered" \
  --as audit-verification
```

## Category-Specific Checklists

Apply only checks required by the original criteria and authorized scope. Use manual reproducers or existing checks; do not author tests, expand scope, or restart services merely because a template mentions coverage.

### LOST Features

```markdown
- [ ] Feature now exists in target codebase
- [ ] Feature has equivalent functionality to source
- [ ] Feature passes the authorized functional checks
- [ ] Feature is documented if originally documented
```

### DEGRADED Features

```markdown
- [ ] Original behavior restored or documented as intentional
- [ ] Performance meets or exceeds original if applicable
- [ ] No new edge case failures introduced
```

### BUG Fixes

```markdown
- [ ] Bug no longer reproducible
- [ ] Fix does not introduce new bugs
- [ ] Original failure and authorized recurrence checks pass
- [ ] Edge cases from ticket addressed
```

### TODO / Stub Completions

```markdown
- [ ] Implementation complete; no placeholder path remains
- [ ] All code paths implemented
- [ ] Error handling in place
- [ ] Authorized checks cover the required behavior
```

### TEST Coverage

```markdown
- [ ] Tests added as specified
- [ ] Tests run and pass
- [ ] Coverage or meaningful behavior coverage improved
- [ ] Edge cases covered
```

### CONFIG Fixes

```markdown
- [ ] Configuration corrected
- [ ] Example/default config updated where needed
- [ ] Required schema-change handling is verified when explicitly in scope
- [ ] Documentation updated
```

### SECURITY Fixes

```markdown
- [ ] Exploit path no longer works
- [ ] Regression coverage exists without exposing secrets
- [ ] No new exposure surface introduced
- [ ] No widened permissions or leaked credentials
```

### CODE-QUALITY Improvements

```markdown
- [ ] Behavior unchanged; existing tests pass
- [ ] Complexity or structural debt reduced
- [ ] Static analysis output equal or improved
- [ ] No new TODO/FIXME markers introduced
```

## Status Meanings

| Status | When to Use |
|--------|-------------|
| `DRAFT` | Incomplete ticket; should not enter resolution |
| `OPEN` | Evidence-ready ticket awaiting implementation |
| `READY_FOR_VERIFICATION` | Fix implemented; awaiting independent verification |
| `PASS` | All acceptance criteria independently verified |
| `PARTIAL` | Some criteria satisfied, others need work |
| `FAIL` | Fix not implemented or fundamentally incorrect |
| `REGRESS` | Was previously passing, now broken |
| `WONTFIX` | Intentionally not fixed, documented decision |
| `BLOCKED` | Cannot verify due missing access/dependency/context |
| `INVALID` | Original ticket is wrong, duplicate, or obsolete |
