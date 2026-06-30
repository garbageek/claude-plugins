# Verification Detail Template

Copy this template when verifying individual tickets.

```markdown
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
```

## CLI Verification Commands

PASS requires criterion evidence for every acceptance criterion:

```bash
audit verify 001 \
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

### LOST Features

```markdown
- [ ] Feature now exists in target codebase
- [ ] Feature has equivalent functionality to source
- [ ] Feature has test coverage
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
- [ ] Test added to prevent recurrence
- [ ] Edge cases from ticket addressed
```

### TODO / Stub Completions

```markdown
- [ ] Implementation complete; no placeholder path remains
- [ ] All code paths implemented
- [ ] Error handling in place
- [ ] Tests cover the implementation
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
- [ ] Migration added if schema changed
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
