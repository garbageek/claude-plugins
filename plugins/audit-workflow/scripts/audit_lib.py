"""
Shared parsing and workflow constants for audit ticket scripts.

Imported by:
- scripts/audit
- scripts/generate_summary.py
- audit-verification/scripts/generate_verification_report.py
"""

from __future__ import annotations

import re
from typing import Optional

VALID_CATEGORIES = {
    "BUG", "DEGRADED", "LOST", "TODO", "TEST",
    "CONFIG", "SECURITY", "CODE-QUALITY",
}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_STATUSES = {
    "DRAFT", "OPEN", "READY_FOR_VERIFICATION", "PASS", "PARTIAL", "FAIL",
    "REGRESS", "BLOCKED", "WONTFIX", "INVALID",
}

# Role-based permissions for workflow actors. Missing/unknown actors are not
# unrestricted: all status-changing commands must pass a known actor explicitly.
ACTOR_ROLES: dict[str, set[str]] = {
    "audit-discovery": {"DRAFT", "OPEN"},
    "audit-resolution": {"READY_FOR_VERIFICATION", "BLOCKED", "WONTFIX"},
    "audit-verification": {
        "PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID",
    },
}

VERIFICATION_STATUSES = {"PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID"}

# Current status -> allowed target statuses. Actor permissions are checked
# separately; a transition must satisfy both lifecycle and role ownership.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"OPEN", "INVALID"},
    "OPEN": {"READY_FOR_VERIFICATION", "BLOCKED", "WONTFIX", "INVALID"},
    "READY_FOR_VERIFICATION": {"PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID"},
    "PARTIAL": {"READY_FOR_VERIFICATION", "PASS", "FAIL", "BLOCKED", "WONTFIX", "INVALID"},
    "FAIL": {"READY_FOR_VERIFICATION", "WONTFIX", "INVALID", "BLOCKED"},
    "REGRESS": {"READY_FOR_VERIFICATION", "PASS", "PARTIAL", "FAIL", "BLOCKED", "WONTFIX", "INVALID"},
    "BLOCKED": {"OPEN", "READY_FOR_VERIFICATION", "PASS", "PARTIAL", "FAIL", "WONTFIX", "INVALID"},
    "PASS": {"REGRESS"},
    "WONTFIX": {"OPEN"},
    "INVALID": {"OPEN"},
}


def allowed_statuses(actor: str) -> set[str] | None:
    """Return statuses this known actor may write. None means unknown actor."""
    return ACTOR_ROLES.get(actor)


def can_set_status(actor: str, status: str) -> bool:
    """Check if a known actor may write this status."""
    allowed = allowed_statuses(actor)
    return allowed is not None and status.upper() in allowed


# Backward-compatible alias used by older callers. This no longer treats unknown
# actors as unrestricted.
def can_transition(actor: str, status: str) -> bool:
    return can_set_status(actor, status)


# Pre-compiled category pattern for filename parsing (longest-first)
CATEGORY_PATTERN = "|".join(sorted(map(re.escape, VALID_CATEGORIES), key=len, reverse=True))


def _field(text: str, label: str) -> str:
    """Extract value from **Label:** `value` or **Label:** value."""
    pattern_strict = rf"\*\*{re.escape(label)}:\*\*\s+`([^`\n]*)`"
    m = re.search(pattern_strict, text)
    if m:
        return m.group(1).strip()
    pattern_fallback = rf"\*\*{re.escape(label)}:\*\*\s+([^\n]+)"
    m = re.search(pattern_fallback, text)
    if m:
        value = m.group(1).strip()
        if value == "``":
            return ""
        if value.startswith("`") and value.endswith("`"):
            return value[1:-1].strip()
        return value
    return ""


def parse_ticket_filename(name: str) -> tuple[Optional[int], str, str]:
    """Parse audit ticket filename: NNN-CATEGORY-slug.md.

    Returns (num, category, slug). category='?' if parsing fails.
    """
    num_match = re.match(r"^(\d+)", name)
    num = int(num_match.group(1)) if num_match else None
    m = re.match(rf"^(\d+)-({CATEGORY_PATTERN})-(.+)\.md$", name)
    category = m.group(2) if m else "?"
    slug = m.group(3) if m else name
    return num, category, slug


def md_cell(value: object) -> str:
    """Escape a value for safe insertion into a Markdown table cell."""
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")
