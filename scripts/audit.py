#!/usr/bin/env python3
"""
audit — project-agnostic audit ticket workflow manager.

Usage:
    audit <command> [options]

Common commands:
    init [--json]
    create <category> --title '...' --severity <level> [--module 'path'] [--evidence '...'] [--acceptance-criterion '...']
    open <id>... --as audit-discovery
    resolve <id>... --fix-commit SHA --evidence '...' --test '...' --as audit-resolution
    verify <id>... --status PASS --verified-commit SHA --criterion 'AC1: pass - ...' --evidence '...' --test '...' --verdict '...' --as audit-verification
    list [--status STATUS] [--category CAT] [--severity SEV] [--unverified] [--json]
    show <id>...
    status <id>... [--json]
    summary [--json]
    next --for resolution|verification [--category CAT] [--severity SEV]
    doctor [--fix]
    export [--json]
    baseline create|compare [--tag TAG]

Run from the project root directory, or pass --root /path/to/project. The plugin uses the bundled CLI directly with an explicit project root: `python3 /path/to/artur-plugins/scripts/audit.py --root /path/to/project ...`. The optional MCP server requires manual registration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from graphlib import CycleError, TopologicalSorter
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

# Canonical workflow model. Keep lifecycle constants and parsers here so CLI
# and MCP execute one runtime implementation instead of mirrored copies.
VALID_CATEGORIES = {
    "BUG", "DEGRADED", "LOST", "TODO", "TEST", "CONFIG", "SECURITY", "CODE-QUALITY",
}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_STATUSES = {
    "DRAFT", "OPEN", "READY_FOR_VERIFICATION", "PASS", "PARTIAL", "FAIL",
    "REGRESS", "BLOCKED", "WONTFIX", "INVALID",
}
VERIFICATION_STATUSES = {"PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID"}
ACTOR_ROLES: dict[str, set[str]] = {
    "audit-discovery": {"DRAFT", "OPEN"},
    "audit-resolution": {"READY_FOR_VERIFICATION", "BLOCKED", "WONTFIX"},
    "audit-verification": {"PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID"},
}
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

CATEGORY_PATTERN = "|".join(sorted(map(re.escape, VALID_CATEGORIES), key=len, reverse=True))

def _markdown_lines(text: str) -> Iterable[tuple[int, int, str, bool]]:
    """Yield line offsets and whether a line is outside fenced code/comments."""
    offset = 0
    fence = ""
    length = 0
    in_comment = False
    for line in text.splitlines(keepends=True):
        active = not fence and not in_comment
        marker = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if marker and marker[1][0] == fence and len(marker[1]) >= length and not marker[2].strip():
                fence = ""
            active = False
        elif in_comment:
            if "-->" in line:
                in_comment = False
            active = False
        elif marker:
            fence, length = marker[1][0], len(marker[1])
            active = False
        elif "<!--" in line:
            in_comment = "-->" not in line[line.index("<!--") + 4:]
            # Inline comments do not hide visible text preceding them.
            active = bool(line.split("<!--", 1)[0].strip())
        yield offset, offset + len(line), line, active
        offset += len(line)


def _metadata_header(text: str) -> str:
    for start, _, line, active in _markdown_lines(text):
        if active and re.match(r"^##(?:[ \t\r\n]|$)", line):
            return text[:start]
    return text


def _header_field_span(text: str, label: str) -> tuple[int, int, str, str] | None:
    pattern = rf"^([ \t]*\*\*{re.escape(label)}:\*\*[ \t]*)([^\r\n]*)"
    for begin, _, line, active in _markdown_lines(_metadata_header(text)):
        if active and (match := re.match(pattern, line)):
            return begin, begin + match.end(), match[1], match[2]
    return None


def _field(text: str, label: str) -> str:
    found = _header_field_span(text, label)
    if found is None:
        return ""
    value = found[3].strip()
    quoted = re.match(r"`([^`]*)`", value)
    return quoted.group(1).strip() if quoted else value


def parse_ticket_filename(name: str) -> tuple[Optional[int], str, str]:
    num_match = re.match(r"^(\d+)", name)
    num = int(num_match.group(1)) if num_match else None
    m = re.match(rf"^(\d+)-({CATEGORY_PATTERN})-(.+)\.md$", name)
    category = m.group(2) if m else "?"
    slug = m.group(3) if m else name
    return num, category, slug

def allowed_statuses(actor: str) -> set[str] | None:
    return ACTOR_ROLES.get(actor)

def can_set_status(actor: str, status: str) -> bool:
    allowed = allowed_statuses(actor)
    return allowed is not None and status.upper() in allowed


# ──────────────────────────────────────────────────────────────────────────────
# Global path handling
# ──────────────────────────────────────────────────────────────────────────────


def _resolve_root() -> Path:
    """Consume one explicit root without silently falling back after invalid input."""
    args = sys.argv[1:]
    cleaned: list[str] = []
    explicit: Optional[str] = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            cleaned.extend(args[index:])
            break
        if arg == "--root" or arg.startswith("--root="):
            if explicit is not None:
                print("Error: specify --root only once", file=sys.stderr)
                sys.exit(2)
            if arg == "--root":
                index += 1
                if index >= len(args) or args[index].startswith("--"):
                    print("Error: --root requires a project directory", file=sys.stderr)
                    sys.exit(2)
                explicit = args[index]
            else:
                explicit = arg.partition("=")[2]
            if not explicit:
                print("Error: --root requires a nonempty project directory", file=sys.stderr)
                sys.exit(2)
        else:
            cleaned.append(arg)
        index += 1

    selected = explicit if explicit is not None else os.environ.get("AUDIT_ROOT")
    path = Path(selected).expanduser().resolve() if selected else Path.cwd().resolve()
    if not path.is_dir():
        label = "--root" if explicit is not None else "AUDIT_ROOT"
        print(f"Error: {label} path does not exist or is not a directory: {path}", file=sys.stderr)
        sys.exit(2)
    if cleaned and cleaned[0] == "help":
        cleaned[0] = "--help"
    sys.argv = [sys.argv[0]] + cleaned
    return path


ROOT = _resolve_root()

TICKETS_DIR = ROOT / "audit" / "tickets"
VERIF_DIR = ROOT / "audit" / "verification" / "details"
TRIAGE_DIR = ROOT / "audit" / "triage"
CREATE_LOCK = ROOT / "audit" / ".create.lock"
_LOCK_DEPTH = 0

_STUB_RE = re.compile(r"^\d+\.md$")
_PLACEHOLDER_RE = re.compile(
    r"<!--.*?-->|\bTODO\b|\{(?![^{}]*(?::|\"|')[^{}]*\})[^{}]+\}",
    re.IGNORECASE | re.DOTALL,
)
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "?": 4, "unknown": 4}
_PLEVEL_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "": 4, "?": 4}
_PASS_LIKE = {"PASS"}
TRIAGE_DECISIONS = {"FIX", "DEFER", "WONTFIX", "DUPLICATE"}
FIX_GROUP_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class AuditError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class ItemResult:
    id: str
    ok: bool
    message: str = ""
    path: str = ""
    status: str = ""
    error: str = ""


@dataclass
class BatchResult:
    ok: bool
    updated: list[ItemResult] = field(default_factory=list)
    failed: list[ItemResult] = field(default_factory=list)
    status: str = ""
    commit_error: str = ""

    def exit_code(self) -> int:
        if self.commit_error:
            return 1
        if self.failed and self.updated:
            return 1
        if self.failed:
            return 1
        return 0

    def to_json(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "updated": [r.__dict__ for r in self.updated],
            "failed": [r.__dict__ for r in self.failed],
            **({"commit_error": self.commit_error} if self.commit_error else {}),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Generic helpers
# ──────────────────────────────────────────────────────────────────────────────


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _ticket_num(name: str) -> Optional[int]:
    m = re.match(r"^(\d+)", name)
    return int(m.group(1)) if m else None


def _parse_id(raw: str) -> int:
    text = str(raw).strip()
    if not re.fullmatch(r"[0-9]+", text) or int(text) < 1:
        raise AuditError(f"invalid ticket id: {raw!r}; use a positive decimal ID", 2)
    return int(text)


def _canonical_ticket_id(raw: str) -> str:
    return f"{_parse_id(str(raw).strip()):03d}"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:60]
    return slug or "ticket"


def _split_ids(value: str) -> list[str]:
    if not value or value.lower() == "none":
        return []
    return [x.strip().zfill(3) for x in re.split(r"[,\s]+", value) if x.strip()]


def _join_ids(values: Iterable[str]) -> str:
    cleaned = sorted({_canonical_ticket_id(str(value)) for value in values}, key=int)
    return ", ".join(cleaned) if cleaned else "none"


def md_cell(value: Any) -> str:
    """Escape a value for safe insertion into a Markdown table cell."""
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _json_print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _write_if_missing(path: Path, text: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _touch_gitkeep(directory: Path) -> bool:
    directory.mkdir(parents=True, exist_ok=True)
    keep = directory / ".gitkeep"
    if keep.exists():
        return False
    keep.write_text("", encoding="utf-8")
    return True


def _audit_readme_text() -> str:
    return """# Audit Workflow

This directory stores machine-managed audit tickets and independent verification records.

## Canonical flow

```text
DRAFT -> OPEN -> READY_FOR_VERIFICATION -> PASS/PARTIAL/FAIL/REGRESS/BLOCKED/WONTFIX/INVALID
```

## First commands

Run `python3 /path/to/artur-plugins/scripts/audit.py --root /path/to/project <command> ...`.
The equivalent MCP tools (`audit_doctor`, `audit_summary`, `audit_next`) are available only if the optional server is explicitly registered.

## Roles

- `audit-discovery`: creates evidence-backed tickets and promotes DRAFT to OPEN.
- `audit-resolution`: implements fixes and stops at READY_FOR_VERIFICATION.
- `audit-verification`: independently verifies and is the only normal role that can PASS.

## Source of truth

Use `python3 /path/to/artur-plugins/scripts/audit.py --root /path/to/project export --json` for automation. An explicitly registered MCP server also offers `audit_export`. Markdown files are human-readable records; lifecycle changes should go through the bundled CLI or its MCP wrapper.
"""


def _triage_readme_text() -> str:
    return """# Audit Triage

Ticket headers own triage decisions, priority, dependencies, and optional fix groups.
Triage reports and roadmaps summarize the exported ticket state; editing reports does not change scheduling.

Apply decisions using `python3 /path/to/artur-plugins/scripts/audit.py --root /path/to/project triage set ...` and `deps add ...`. If MCP is explicitly registered, `audit_triage_set` and `audit_dependency_add` are also available.

`next --for resolution` selects the highest-priority unblocked FIX ticket and suggests available tickets in the same fix group or source file for a shared edit session.

Dependency semantics: `003 blocks 001`, so ticket 001 waits until ticket 003 is resolved.
"""


def _initialize_audit_tree(write_docs: bool = True) -> dict[str, Any]:
    created_dirs: list[str] = []
    created_files: list[str] = []
    dirs = [
        TICKETS_DIR,
        VERIF_DIR,
        TRIAGE_DIR,
        ROOT / "audit" / "baselines",
    ]
    for directory in dirs:
        existed = directory.is_dir()
        directory.mkdir(parents=True, exist_ok=True)
        if not existed:
            created_dirs.append(_rel(directory))
        if _touch_gitkeep(directory):
            created_files.append(_rel(directory / ".gitkeep"))
    if write_docs:
        if _write_if_missing(ROOT / "audit" / "README.md", _audit_readme_text()):
            created_files.append(_rel(ROOT / "audit" / "README.md"))
        if _write_if_missing(TRIAGE_DIR / "README.md", _triage_readme_text()):
            created_files.append(_rel(TRIAGE_DIR / "README.md"))
    return {
        "ok": True,
        "root": str(ROOT),
        "created_dirs": created_dirs,
        "created_files": created_files,
        "already_initialized": not created_dirs and not created_files,
    }


@contextmanager
def _create_lock_cm(*, read_only: bool = False):
    """Serialize local CLI access on POSIX and Windows; never silently skip a failed lock."""
    global _LOCK_DEPTH
    if _LOCK_DEPTH:
        yield
        return
    if read_only and not CREATE_LOCK.exists():
        yield
        return
    if not read_only:
        CREATE_LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = CREATE_LOCK.open("rb" if read_only else "a+b")
    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                mode = fcntl.LOCK_SH if read_only else fcntl.LOCK_EX
                fcntl.flock(handle.fileno(), mode | fcntl.LOCK_NB)
            locked = True
        except (OSError, ImportError) as exc:
            raise AuditError(f"audit lock unavailable: {CREATE_LOCK}: {exc}", 1) from exc
        _LOCK_DEPTH += 1
        try:
            yield
        finally:
            _LOCK_DEPTH -= 1
    finally:
        if locked:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_documents(updates: dict[Path, str]) -> None:
    """Stage complete files, then replace them; roll back earlier replacements on I/O failure."""
    originals: dict[Path, bytes | None] = {}
    staged: dict[Path, Path] = {}
    replaced: list[Path] = []

    def stage(path: Path, data: bytes) -> Path:
        fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temp = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            temp.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
            return temp
        except BaseException:
            temp.unlink(missing_ok=True)
            raise

    try:
        for path, text in updates.items():
            old = path.read_bytes() if path.exists() else None
            data = text.encode("utf-8")
            if old == data:
                continue
            originals[path] = old
            staged[path] = stage(path, data)
        for path, temp in staged.items():
            os.replace(temp, path)
            replaced.append(path)
    except BaseException as exc:
        errors = []
        for path in reversed(replaced):
            backup = None
            try:
                old = originals[path]
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    backup = stage(path, old)
                    os.replace(backup, path)
            except OSError as rollback_error:
                errors.append(f"{path}: {rollback_error}")
            finally:
                if backup is not None:
                    backup.unlink(missing_ok=True)
        if isinstance(exc, OSError):
            detail = f"; rollback failed: {'; '.join(errors)}" if errors else "; no record changes retained"
            raise AuditError(f"unable to write audit records: {exc}{detail}", 1) from exc
        raise
    finally:
        for temp in staged.values():
            temp.unlink(missing_ok=True)


def _named_verif_files() -> list[Path]:
    return sorted(VERIF_DIR.glob("*.md")) if VERIF_DIR.is_dir() else []


def _all_ticket_files() -> list[Path]:
    if not TICKETS_DIR.is_dir():
        return []
    return sorted(TICKETS_DIR.glob("*.md"))


def _existing_ticket_numbers() -> set[int]:
    nums: set[int] = set()
    for path in list(_all_ticket_files()) + list(_named_verif_files()):
        num = _ticket_num(path.name)
        if num is not None:
            nums.add(num)
    return nums


def _next_ticket_number() -> int:
    existing = _existing_ticket_numbers()
    return (max(existing) + 1) if existing else 1


def _unique_record(paths: Iterable[Path], num: int, kind: str) -> Optional[Path]:
    candidates = sorted({path for path in paths if _ticket_num(path.name) == num})
    if len(candidates) > 1:
        raise AuditError(f"duplicate {kind} number {num:03d}: " + ", ".join(p.name for p in candidates), 1)
    if not candidates:
        return None
    path = candidates[0]
    parsed_num, category, _ = parse_ticket_filename(path.name)
    if parsed_num is None or parsed_num < 1 or category not in VALID_CATEGORIES:
        raise AuditError(f"invalid {kind} filename: {path.name}; use NNN-CATEGORY-slug.md", 1)
    return path


def _ticket_for(num: int) -> Optional[Path]:
    return _unique_record(_all_ticket_files(), num, "ticket")


def _verif_for(num: int, ticket_path: Optional[Path] = None) -> Optional[Path]:
    path = _unique_record(_named_verif_files(), num, "verification")
    if path and ticket_path and path.name != ticket_path.name:
        raise AuditError(f"ticket/verification name mismatch: {ticket_path.name} vs {path.name}", 1)
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Markdown parsing/updating
# ──────────────────────────────────────────────────────────────────────────────


def _replace_field(text: str, label: str, value: str) -> str:
    if any(char in value for char in ("\n", "\r", "`")):
        raise AuditError(f"{label} must be a single-line value without backticks", 2)
    found = _header_field_span(text, label)
    if found is None:
        return text
    start, end, prefix, _ = found
    return text[:start] + f"{prefix.rstrip()} `{value}`" + text[end:]


def _ensure_field_after(text: str, after_label: str, label: str, value: str) -> str:
    if any(char in value for char in ("\n", "\r", "`")):
        raise AuditError(f"{label} must be a single-line value without backticks", 2)
    if _header_field_span(text, label) is not None:
        return _replace_field(text, label, value)
    anchor = _header_field_span(text, after_label)
    if anchor is not None:
        return text[:anchor[1]] + f"\n**{label}:** `{value}`" + text[anchor[1]:]
    header = _metadata_header(text)
    return header.rstrip() + f"\n**{label}:** `{value}`\n\n" + text[len(header):]


def _set_ticket_field(text: str, after_label: str, label: str, value: str) -> str:
    """Write a ticket header field, inserting it when absent; never report false success."""
    updated = _ensure_field_after(text, after_label, label, value)
    if _header_field_span(updated, label) is None or _field(updated, label) != value:
        raise AuditError(f"unable to set ticket field {label}", 1)
    return updated


def _section_span(text: str, section: str) -> tuple[int, int] | None:
    start = None
    for begin, end, line, active in _markdown_lines(text):
        if not active or not re.match(r"^##(?:[ \t\r\n]|$)", line):
            continue
        if start is not None:
            return start, begin
        if line.rstrip("\r\n \t") == section:
            start = end
    return (start, len(text)) if start is not None else None


def _section_content(text: str, section: str) -> str:
    span = _section_span(text, section)
    return text[span[0]:span[1]].strip() if span else ""


def _replace_section(text: str, section: str, body: str) -> str:
    body = body.strip()
    span = _section_span(text, section)
    if span is None:
        return text.rstrip() + f"\n\n{section}\n\n{body}\n"
    start, end = span
    return text[:start].rstrip("\r\n") + f"\n\n{body}\n\n" + text[end:].lstrip("\r\n")


def _append_to_section(text: str, section: str, content: str) -> str:
    existing = _section_content(text, section)
    if existing:
        new_body = existing.rstrip() + "\n" + content.strip()
    else:
        new_body = content.strip()
    return _replace_section(text, section, new_body)


def _meaningful_content(content: str) -> bool:
    cleaned = _PLACEHOLDER_RE.sub("", content)
    for line in cleaned.splitlines():
        line = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", line)
        line = re.sub(r"^\[[ xX]\]\s*", "", line)
        line = re.sub(r"^AC\d+\s*[:.-]\s*", "", line, flags=re.IGNORECASE)
        line = re.sub(r"^\*\*[A-Z_]+\*\*\s*$", "", line)
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            continue
        if line.strip(" \t`*_#-:[]"):
            return True
    return False


def _has_nonplaceholder_content(text: str, section: str) -> bool:
    return _meaningful_content(_section_content(text, section))


def _criterion_definitions(items: Sequence[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    used: set[str] = set()
    for item in items:
        raw = re.sub(r"^\s*[-*+]\s*(?:\[[ xX]\]\s*)?", "", item).strip()
        match = re.match(r"^(AC\d+)\s*[:.-]\s*(.*)$", raw, re.IGNORECASE)
        cid, description = (match[1].upper(), match[2].strip()) if match else ("", raw)
        if cid:
            if cid in used:
                raise AuditError(f"duplicate acceptance criterion {cid}", 2)
            used.add(cid)
        parsed.append((cid, description))
    result: list[tuple[str, str]] = []
    next_id = 1
    for cid, description in parsed:
        if not cid:
            while f"AC{next_id}" in used:
                next_id += 1
            cid = f"AC{next_id}"
            used.add(cid)
        result.append((cid, description))
    return result


def _acceptance_criteria(ticket_text: str) -> dict[str, str]:
    content = _section_content(ticket_text, "## Acceptance Criteria")
    items = [
        line.strip() for _, _, line, active in _markdown_lines(content)
        if active and re.match(r"^\s*[-*+]\s+", line)
    ]
    return {
        cid: description for cid, description in _criterion_definitions(items)
        if _meaningful_content(description)
    }


_CRITERION_RESULT_RE = re.compile(
    r"^\s*(?:-\s*(?:\[[ xX]\]\s*)?)?(AC\d+)\s*[:.-]\s*(pass|fail|partial|blocked|regress)\b",
    re.IGNORECASE,
)


def _criterion_result(raw: str) -> tuple[str, str] | None:
    match = _CRITERION_RESULT_RE.match(raw.strip())
    if not match:
        return None
    return match.group(1).upper(), match.group(2).lower()


def _criteria_result_ids(text: str) -> set[str]:
    # Later entries within one section supersede earlier entries. Separate
    # sections have no shared timestamps: conflicting active results cannot PASS.
    states: dict[str, set[str]] = {}
    for section in ("## Criteria Results", "## Verification Checklist"):
        latest: dict[str, str] = {}
        for _, _, line, active in _markdown_lines(_section_content(text, section)):
            parsed = _criterion_result(line) if active else None
            if parsed:
                latest[parsed[0]] = parsed[1]
        for cid, result in latest.items():
            states.setdefault(cid, set()).add(result)
    return {cid for cid, results in states.items() if results == {"pass"}}


def _append_criterion_results(text: str, criteria: Sequence[str]) -> str:
    lines: list[str] = []
    updated_ids: set[str] = set()
    for raw in criteria:
        raw = raw.strip()
        if not raw:
            continue
        if "\n" in raw or "\r" in raw:
            raise AuditError("each --criterion must be one line; repeat --criterion for additional results", 2)
        parsed = _criterion_result(raw)
        if not parsed:
            raise AuditError(f"invalid criterion result: {raw!r}; use 'AC1: pass - observed result'", 2)
        updated_ids.add(parsed[0])
        lines.append(f"- [{'x' if parsed and parsed[1] == 'pass' else ' '}] {raw}")
    if not lines:
        return text

    # Preserve superseded checklist proof before the fresh CLI result. Leaving
    # contradictory copies active would make a valid new PASS fail doctor.
    checklist = _section_content(text, "## Verification Checklist")
    if checklist and updated_ids:
        kept: list[str] = []
        superseded: list[str] = []
        for _, _, line, active in _markdown_lines(checklist):
            parsed = _criterion_result(line) if active else None
            (superseded if parsed and parsed[0] in updated_ids else kept).append(line.rstrip("\r\n"))
        if superseded:
            text = _append_to_section(text, "## Criteria Results", "\n".join(superseded))
            text = _replace_section(text, "## Verification Checklist", "\n".join(kept))
    return _append_to_section(text, "## Criteria Results", "\n".join(lines))


def _evidence_text(items: Sequence[str]) -> str:
    return "\n\n".join(
        item.strip() if "\n" in item or "\r" in item else f"- {item.strip()}"
        for item in items if item.strip()
    )


def _archive_verification(text: str, *, include_resolution: bool) -> str:
    """Retain previous proof as history, outside the active evidence sections."""
    sections = ["Criteria Results", "Verification Checklist", "Evidence", "Test Verification", "Verdict"]
    if include_resolution:
        sections = ["Resolution Evidence", "Current State", *sections]
    fields = ["Verified Date", "Verified By", "Verified Commit"]
    proof_sections = [section for section in sections if section != "Verdict"]
    # The default OPEN verdict and unchecked checklist are not verification
    # proof. Archiving them on the first resolve creates meaningless history.
    has_proof = any(_has_nonplaceholder_content(text, f"## {section}") for section in proof_sections)
    has_proof |= any(_field(text, label) for label in ["Resolved By", "Fix Commit", *fields])
    if has_proof:
        snapshot = [f"### Archived at {datetime.now().isoformat(timespec='seconds')}"]
        for label in ["Verification Status", "Resolved Date", "Resolved By", "Fix Commit", *fields]:
            value = _field(text, label)
            if value:
                snapshot.append(f"**{label}:** `{value}`")
        for section in sections:
            content = _section_content(text, f"## {section}")
            if content and _has_nonplaceholder_content(text, f"## {section}"):
                if section == "Verdict" and _field(text, "Verification Status") == "OPEN":
                    continue
                # Archived headings must not be parsed as active ## sections.
                content = "".join(
                    re.sub(r"^(#{2,})[ \t]", r"#\1 ", line) if active else line
                    for _, _, line, active in _markdown_lines(content)
                )
                snapshot.append(f"#### {section}\n\n{content}")
        text = _append_to_section(text, "## Verification History", "\n\n".join(snapshot))
    for section in sections:
        text = _replace_section(text, f"## {section}", "")
    for label in fields:
        text = _replace_field(text, label, "")
    return text


def _history_header() -> str:
    return "| Time | Status | Commit | Actor | Verdict |\n|---|---|---|---|---|\n"


def _append_history(text: str, status: str, commit: str, actor: str, verdict: str) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    line = f"| {md_cell(now)} | `{md_cell(status)}` | `{md_cell(commit)}` | {md_cell(actor)} | {md_cell(verdict)} |"
    content = _section_content(text, "## Status History")
    header = _history_header()
    if content.startswith(header.rstrip()):
        content = header + line + "\n" + content[len(header.rstrip()):].lstrip("\r\n")
    else:
        content = header + line + ("\n" + content if content else "")
    return _replace_section(text, "## Status History", content)


# ──────────────────────────────────────────────────────────────────────────────
# Canonical parsing/model
# ──────────────────────────────────────────────────────────────────────────────


def parse_ticket(path: Path, text: Optional[str] = None) -> dict[str, Any]:
    name = path.name
    num, category, slug = parse_ticket_filename(name)
    text = path.read_text(encoding="utf-8") if text is None else text
    severity = _field(text, "Severity") or "?"
    module = _field(text, "Module") or "?"
    title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else slug
    return {
        "num": num,
        "id": f"{num:03d}" if num is not None else "???",
        "category": category,
        "slug": slug,
        "severity": severity.lower(),
        "module": module,
        "title": title,
        "depends_on": _split_ids(_field(text, "Depends On")),
        "blocks": _split_ids(_field(text, "Blocks")),
        "impact": _field(text, "Impact"),
        "effort": _field(text, "Effort"),
        "priority": _field(text, "Priority"),
        "p_level": _field(text, "P-level").upper(),
        "decision": _field(text, "Decision").upper(),
        "phase": _field(text, "Phase"),
        "fix_group": _field(text, "Fix Group"),
        "path": str(path),
        "_path": path,
        "_text": text,
    }


def parse_verification(path: Path) -> dict[str, Any]:
    name = path.name
    num = _ticket_num(name)
    text = path.read_text(encoding="utf-8", errors="replace")
    status = _field(text, "Verification Status") or "?"
    return {
        "num": num,
        "id": f"{num:03d}" if num is not None else "???",
        "status": status.upper(),
        "resolved_date": _field(text, "Resolved Date"),
        "resolved_by": _field(text, "Resolved By"),
        "verified_date": _field(text, "Verified Date"),
        "verified_by": _field(text, "Verified By") or "",
        "commit": _field(text, "Fix Commit") or "",
        "verified_commit": _field(text, "Verified Commit"),
        "verdict": _section_content(text, "## Verdict"),
        "evidence": _section_content(text, "## Evidence"),
        "path": str(path),
        "_path": path,
        "_text": text,
    }


def load_records() -> list[dict[str, Any]]:
    verif_index: dict[int, dict[str, Any]] = {}
    for path in _named_verif_files():
        v = parse_verification(path)
        if v["num"] is not None:
            if v["num"] in verif_index:
                raise AuditError(f"duplicate verification number {v['id']}; run doctor", 1)
            verif_index[v["num"]] = v

    records: list[dict[str, Any]] = []
    seen: set[int] = set()
    for path in _all_ticket_files():
        t = parse_ticket(path)
        num = t["num"]
        if num is None or num < 1 or t["category"] not in VALID_CATEGORIES:
            raise AuditError(f"invalid ticket filename: {path.name}; run doctor", 1)
        if num in seen:
            raise AuditError(f"duplicate ticket number {t['id']}; run doctor", 1)
        seen.add(num)
        v = verif_index.get(num, {})
        if v and Path(v["path"]).name != path.name:
            raise AuditError(f"ticket/verification name mismatch for {t['id']}; run doctor", 1)
        record = {
            **{k: v2 for k, v2 in t.items() if not k.startswith("_")},
            "status": v.get("status", "UNVERIFIED"),
            "verification_path": v.get("path", ""),
            "resolved_date": v.get("resolved_date", ""),
            "resolved_by": v.get("resolved_by", ""),
            "fix_commit": v.get("commit", ""),
            "verified_date": v.get("verified_date", ""),
            "verified_by": v.get("verified_by", ""),
            "verified_commit": v.get("verified_commit", ""),
            "verdict": v.get("verdict", ""),
            "verification_evidence": v.get("evidence", ""),
            "ticket_hash": _hash_file(path),
            "verification_hash": _hash_file(Path(v["path"])) if v.get("path") else "",
        }
        records.append(record)

    ticket_nums = {r["num"] for r in records if r["num"] is not None}
    for v in verif_index.values():
        if v["num"] not in ticket_nums:
            records.append({
                "num": v["num"],
                "id": v["id"],
                "category": "?",
                "slug": Path(v["path"]).stem,
                "severity": "?",
                "module": "",
                "title": f"[orphaned verif] {Path(v['path']).name}",
                "path": "",
                "status": v["status"],
                "verification_path": v["path"],
                "verdict": v.get("verdict", ""),
                "verification_evidence": v.get("evidence", ""),
                "depends_on": [],
                "blocks": [],
            })
    return sorted(records, key=lambda r: (r.get("num") is None, r.get("num") or 10**9))


# ──────────────────────────────────────────────────────────────────────────────
# Validation and transitions
# ──────────────────────────────────────────────────────────────────────────────


def _require_actor(actor: str, target_status: str) -> None:
    if not actor:
        raise AuditError("--as is required for status-changing commands", 2)
    if actor not in ACTOR_ROLES:
        raise AuditError(f"unknown actor '{actor}'. Valid: {', '.join(sorted(ACTOR_ROLES))}", 2)
    if not can_set_status(actor, target_status):
        allowed = allowed_statuses(actor) or set()
        raise AuditError(
            f"{actor} cannot set {target_status}. Allowed: {', '.join(sorted(allowed)) or 'none'}",
            2,
        )


def _validate_transition(current: str, target: str) -> None:
    current = (current or "UNVERIFIED").upper()
    target = target.upper()
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target == current:
        # Allow idempotent refresh of metadata for non-terminal in-progress states.
        if target in {"DRAFT", "OPEN", "READY_FOR_VERIFICATION", "BLOCKED"}:
            return
    if target not in allowed:
        raise AuditError(f"invalid transition: {current} -> {target}", 2)


def _ticket_ready_for_open(ticket_text: str) -> tuple[bool, list[str]]:
    missing = [
        section for section in ("## Description", "## Evidence", "## Suggested Verification")
        if not _has_nonplaceholder_content(ticket_text, section)
    ]
    try:
        if not _acceptance_criteria(ticket_text):
            missing.append("## Acceptance Criteria")
    except AuditError as exc:
        missing.append(exc.message)
    return not missing, missing


def _pass_ready(ticket_path: Path, verif_text: str) -> tuple[bool, list[str]]:
    ticket_text = ticket_path.read_text(encoding="utf-8")
    missing: list[str] = []
    try:
        criteria = _acceptance_criteria(ticket_text)
    except AuditError as exc:
        return False, [exc.message]
    if not criteria:
        missing.append("ticket has no non-placeholder acceptance criteria")
    passing = _criteria_result_ids(verif_text)
    for cid in criteria:
        if cid not in passing:
            missing.append(f"missing passing evidence for {cid}")
    if not _has_nonplaceholder_content(verif_text, "## Evidence"):
        missing.append("verification evidence is empty")
    if not _has_nonplaceholder_content(verif_text, "## Test Verification"):
        missing.append("test verification is empty")
    verdict = _section_content(verif_text, "## Verdict")
    if not _meaningful_content(verdict):
        missing.append("verdict is empty")
    elif (label := re.match(r"^\*\*(\w+)\*\*", verdict)) and label.group(1).upper() != "PASS":
        missing.append(f"verdict status is {label.group(1)}, not PASS")
    return not missing, missing


def _validate_transition_requirements(target: str, ticket_path: Optional[Path], verif_text: str) -> None:
    """Validate the record that will actually be persisted, not CLI argument truthiness."""
    if ticket_path is None:
        raise AuditError(f"{target} requires an existing ticket file", 2)
    if target not in {"DRAFT", "INVALID", "WONTFIX"}:
        ready, missing = _ticket_ready_for_open(ticket_path.read_text(encoding="utf-8"))
        if not ready:
            raise AuditError(f"{target} requires evidence-ready ticket content; missing: {', '.join(missing)}", 2)
    if target == "READY_FOR_VERIFICATION":
        if not _meaningful_content(_field(verif_text, "Fix Commit")):
            raise AuditError("READY_FOR_VERIFICATION requires --fix-commit", 2)
        if not _has_nonplaceholder_content(verif_text, "## Resolution Evidence"):
            raise AuditError("READY_FOR_VERIFICATION requires non-placeholder resolution evidence", 2)
        if not _has_nonplaceholder_content(verif_text, "## Test Verification"):
            raise AuditError("READY_FOR_VERIFICATION requires non-placeholder test verification", 2)
    elif target == "PASS":
        ok, missing = _pass_ready(ticket_path, verif_text)
        if not ok:
            raise AuditError("PASS requirements not met: " + "; ".join(missing), 2)
        if not _meaningful_content(_field(verif_text, "Verified Commit")):
            raise AuditError("PASS requires --verified-commit or existing Verified Commit", 2)
    if target in {"WONTFIX", "INVALID", "BLOCKED"}:
        verdict = _section_content(verif_text, "## Verdict")
        label = re.match(r"^\*\*(\w+)\*\*", verdict)
        if not _meaningful_content(verdict) or (label and label[1].upper() != target):
            raise AuditError(f"{target} requires --reason or --verdict rationale for this status", 2)


# ──────────────────────────────────────────────────────────────────────────────
# Git helpers
# ──────────────────────────────────────────────────────────────────────────────


def _inside_git_repo() -> bool:
    try:
        result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, capture_output=True, text=True)
    except OSError as exc:
        raise AuditError(f"unable to run git: {exc}", 1) from exc
    return result.returncode == 0 and result.stdout.strip() == "true"


def _ensure_clean_worktree(allow_dirty: bool = False) -> None:
    if not _inside_git_repo():
        raise AuditError("--git-commit requires a Git worktree; no records were changed", 1)
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", ".", ":(exclude)audit/.create.lock"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if result.returncode:
        raise AuditError("unable to inspect worktree: " + result.stderr.strip(), 1)
    if result.stdout.strip() and not allow_dirty:
        raise AuditError(
            "dirty worktree before audit metadata commit; commit/stash changes or pass --allow-dirty\n"
            + result.stdout.strip(), 1,
        )


def _git_commit(paths: Sequence[Path], message: str, allow_dirty: bool = False) -> str:
    if not paths:
        return ""
    # Preflight already ran before mutations. Only these files belong in the
    # metadata commit; unrelated staged work must remain staged.
    names = [str(path) for path in dict.fromkeys(paths)]
    add = subprocess.run(["git", "add", "-f", "--", *names], cwd=ROOT, capture_output=True, text=True)
    if add.returncode:
        raise AuditError("git add failed: " + (add.stderr.strip() or add.stdout.strip()), 1)
    result = subprocess.run(["git", "commit", "--only", "-m", message, "--", *names], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise AuditError("git commit failed: " + (result.stderr.strip() or result.stdout.strip()), 1)
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return sha.stdout.strip() if sha.returncode == 0 else ""


def _hash_file(path: Path) -> str:
    if not path or not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# File writers
# ──────────────────────────────────────────────────────────────────────────────


def _infer_source() -> str:
    agent = os.environ.get("AGENT_NAME", "")
    return f"code review by {agent}" if agent else "code review"


def _ticket_text(
    *,
    title: str,
    category: str,
    severity: str,
    module: str,
    lines: str,
    source: str,
    depends_on: Sequence[str],
    blocks: Sequence[str],
    description: Optional[str],
    expected: Optional[str],
    actual: Optional[str],
    evidence: Sequence[str],
    recommendation: Optional[str],
    criteria: Sequence[str],
    suggested_verification: Optional[str],
) -> str:
    desc = description or "<!-- TODO: Add a clear, factual description of the issue. -->"
    exp = expected or "<!-- TODO: What should happen according to requirements, design, or user expectations. -->"
    act = actual or "<!-- TODO: What actually happens. Include error messages, wrong output, crash details. -->"
    ev = _evidence_text(evidence) if evidence else "<!-- TODO: Add concrete evidence: code snippets, log lines, traces, reproduction steps. -->"
    rec = recommendation or "<!-- TODO: Add actionable fix: what to change, where, and why. -->"
    if criteria:
        if any("\n" in item or "\r" in item for item in criteria):
            raise AuditError("each --acceptance-criterion must be one line; repeat the option", 2)
        ac = "\n".join(f"- [ ] {cid}: {description}" for cid, description in _criterion_definitions(criteria))
    else:
        ac = "- [ ] <!-- TODO: AC1: observable, testable condition that resolves the issue. -->"
    sv = suggested_verification or "<!-- TODO: specific test commands, reproduction steps, or assertions an independent verifier should run. -->"
    return (
        f"# {title}\n\n"
        f"**Category:** `{category}`\n"
        f"**Severity:** `{severity}`\n"
        f"**Module:** `{module}`\n"
        f"**Lines:** `{lines}`\n"
        f"**Source:** `{source}`\n"
        f"**Depends On:** `{_join_ids(depends_on)}`\n"
        f"**Blocks:** `{_join_ids(blocks)}`\n"
        f"**Impact:** ``\n"
        f"**Effort:** ``\n"
        f"**Priority:** ``\n"
        f"**P-level:** ``\n"
        f"**Decision:** `FIX`\n"
        f"**Phase:** ``\n"
        f"**Fix Group:** ``\n\n"
        f"## Description\n\n{desc}\n\n"
        f"## Expected Behavior\n\n{exp}\n\n"
        f"## Actual Behavior\n\n{act}\n\n"
        f"## Evidence\n\n{ev}\n\n"
        f"## Recommendation\n\n{rec}\n\n"
        f"## Acceptance Criteria\n\n{ac}\n\n"
        f"## Suggested Verification\n\n{sv}\n"
    )


def _verification_text(num: int, category: str, severity: str, slug: str, status: str) -> str:
    return (
        f"# Verification: {num:03d}-{category}-{slug}\n\n"
        f"**Original Ticket:** `audit/tickets/{num:03d}-{category}-{slug}.md`\n"
        f"**Original Category:** `{category}`\n"
        f"**Original Severity:** `{severity}`\n"
        f"**Verification Status:** `{status}`\n"
        f"**Resolved Date:** ``\n"
        f"**Resolved By:** ``\n"
        f"**Verified Date:** ``\n"
        f"**Verified By:** ``\n"
        f"**Fix Commit:** ``\n"
        f"**Verified Commit:** ``\n\n"
        f"## Original Issue\n\n"
        f"## Resolution Evidence\n\n"
        f"## Criteria Results\n\n"
        f"## Verification Checklist\n\n- [ ] \n\n"
        f"## Current State\n\n"
        f"## Evidence\n\n"
        f"## Test Verification\n\n"
        f"## Verdict\n\n"
        f"## Verification History\n\n"
    )


def _write_stub_verification(vpath: Path, num: int, ticket_path: Path) -> None:
    t = parse_ticket(ticket_path)
    status = "DRAFT" if not _ticket_ready_for_open(t["_text"])[0] else "OPEN"
    text = _verification_text(num, t["category"], t["severity"], t["slug"], status)
    _write_documents({vpath: text})


# ──────────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> None:
    result = _initialize_audit_tree(write_docs=not getattr(args, "no_docs", False))
    if args.json:
        _json_print(result)
        return
    if result["already_initialized"]:
        print(f"Audit workflow already initialized at {_rel(ROOT / 'audit')}")
        return
    print(f"Initialized audit workflow at {_rel(ROOT / 'audit')}")
    if result["created_dirs"]:
        print("Created directories:")
        for item in result["created_dirs"]:
            print(f"  - {item}")
    if result["created_files"]:
        print("Created files:")
        for item in result["created_files"]:
            print(f"  - {item}")


def cmd_create(args: argparse.Namespace) -> dict[str, Any]:
    cat = (args.category or "").upper()
    if cat not in VALID_CATEGORIES:
        raise AuditError(f"unknown category '{args.category}'. Valid: {', '.join(sorted(VALID_CATEGORIES))}", 2)
    sev = args.severity.lower()
    if sev not in VALID_SEVERITIES:
        raise AuditError(f"unknown severity '{args.severity}'. Valid: {', '.join(sorted(VALID_SEVERITIES))}", 2)

    for label, value in (("Title", args.title), ("Module", args.module), ("Lines", args.lines), ("Source", args.source or "")):
        if any(char in value for char in ("\n", "\r", "`")):
            raise AuditError(f"{label} must be a single-line value without backticks", 2)
    if not args.title.strip():
        raise AuditError("title must be nonempty", 2)
    slug = _slugify(args.title)
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    VERIF_DIR.mkdir(parents=True, exist_ok=True)

    ticket_body = _ticket_text(
        title=args.title,
        category=cat,
        severity=sev,
        module=args.module,
        lines=args.lines,
        source=args.source or _infer_source(),
        depends_on=args.depends_on or [],
        blocks=args.blocks or [],
        description=args.description,
        expected=args.expected,
        actual=args.actual,
        evidence=args.evidence or [],
        recommendation=args.recommendation,
        criteria=args.acceptance_criterion or [],
        suggested_verification=args.suggested_verification,
    )
    ready, missing = _ticket_ready_for_open(ticket_body)
    if args.open and not ready:
        raise AuditError(f"--open requires evidence-ready content; missing: {', '.join(missing)}", 2)
    status = "OPEN" if ready else "DRAFT"

    with _create_lock_cm():
        next_num = _next_ticket_number()
        source_id = f"{next_num:03d}"
        dep_ids = {_canonical_ticket_id(x) for x in (args.depends_on or [])}
        block_ids = {_canonical_ticket_id(x) for x in (args.blocks or [])}
        if source_id in dep_ids or source_id in block_ids:
            raise AuditError("a ticket cannot depend on or block itself", 2)
        for ref in sorted(dep_ids | block_ids):
            if not _ticket_for(_parse_id(ref)):
                raise AuditError(f"ticket {ref} not found", 1)

        ticket_name = f"{next_num:03d}-{cat}-{slug}.md"
        verif_name = ticket_name
        ticket_path = TICKETS_DIR / ticket_name
        verif_path = VERIF_DIR / verif_name
        if ticket_path.exists() or verif_path.exists():
            raise AuditError("ticket allocator selected an occupied number; retry after resolving numbering drift", 1)
        pending = {
            ticket_path: ticket_body,
            verif_path: _verification_text(next_num, cat, sev, slug, status),
        }
        if dep_ids or block_ids:
            _mutate_dependencies(
                source_id, depends_on=sorted(dep_ids), blocks=sorted(block_ids),
                remove=False, pending=pending,
            )
        else:
            _write_documents(pending)

    result = {
        "ok": True,
        "num": f"{next_num:03d}",
        "status": status,
        "ticket": _rel(ticket_path),
        "verification": _rel(verif_path),
    }
    if args.json:
        _json_print(result)
    else:
        print(f"Created ticket:       {_rel(ticket_path)}")
        print(f"Created verification: {_rel(verif_path)}")
        print(f"Initial status:       {status}")
    return result


def _status_matches(ver_status: str, filters: Optional[Sequence[str]]) -> bool:
    if not filters:
        return True
    wanted = {s.upper() for s in filters}
    if ver_status in wanted:
        return True
    return "UNVERIFIED" in wanted and ver_status == "UNVERIFIED"


def cmd_list(args: argparse.Namespace) -> None:
    rows = []
    for r in load_records():
        if not _status_matches(r.get("status", ""), args.status):
            continue
        if args.category and r.get("category") != args.category.upper():
            continue
        if args.severity and str(r.get("severity", "")).lower() != args.severity.lower():
            continue
        if args.unverified and r.get("status") not in {"UNVERIFIED", "DRAFT", "OPEN"}:
            continue
        rows.append(r)
    if args.json:
        _json_print(rows)
        return
    if not rows:
        print("No tickets match.")
        return
    print(f"{'#':<4}  {'Category':<14}  {'Severity':<8}  {'Status':<22}  {'P':<3}  Title")
    print("-" * 90)
    for r in rows:
        print(
            f"{r.get('id', '???'):<4}  {r.get('category', '?'):<14}  {r.get('severity', '?'):<8}  "
            f"{r.get('status', '?'):<22}  {r.get('p_level', ''):<3}  {str(r.get('title', ''))[:45]}"
        )
    print(f"\n{len(rows)} tickets")


def cmd_summary(args: argparse.Namespace) -> None:
    counts = Counter(r.get("status", "UNKNOWN") for r in load_records())
    total = sum(counts.values())
    if args.json:
        _json_print({"total": total, "counts": dict(sorted(counts.items()))})
        return
    if total == 0:
        print("No tickets found.")
        return
    print(f"Tickets: {total} | " + " | ".join(f"{k}: {v}" for k, v in sorted(counts.items())))


def cmd_status(args: argparse.Namespace) -> None:
    results: dict[str, Any] = {}
    exit_failed = False
    for raw in dict.fromkeys(args.id):
        try:
            num = _parse_id(raw)
            path = _verif_for(num, _ticket_for(num))
        except AuditError as exc:
            results[raw] = {"error": exc.message}
            exit_failed = True
            continue
        if path is None:
            results[f"{num:03d}"] = {"status": "NO FILE"}
            exit_failed = True
        else:
            v = parse_verification(path)
            results[f"{num:03d}"] = {"status": v["status"], "path": _rel(path)}
    if args.json:
        _json_print(results)
    else:
        for tid, data in results.items():
            if "error" in data:
                print(f"{tid}: {data['error']}")
            else:
                print(f"{tid}: {data['status']:<22} {data.get('path', '')}")
    if exit_failed:
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    if not args.id:
        raise AuditError("Usage: audit show <ticket_id>...", 2)
    found_any = False
    failed = False
    first = True
    for raw in dict.fromkeys(args.id):
        try:
            num = _parse_id(raw)
        except AuditError as exc:
            print(f"{raw}: {exc}", file=sys.stderr)
            failed = True
            continue
        ticket_path = _ticket_for(num)
        verif_path = _verif_for(num, ticket_path)
        if not ticket_path and not verif_path:
            print(f"{num:03d}: ticket not found", file=sys.stderr)
            failed = True
            continue
        found_any = True
        sep = "─" * 70
        if not first:
            print("\n" + sep + "\n")
        first = False
        print(sep)
        if ticket_path:
            print(f"TICKET: {ticket_path.name}")
            print(sep)
            print(ticket_path.read_text(encoding="utf-8", errors="replace").rstrip())
        else:
            print(f"{num:03d}: no ticket file found")
        if verif_path:
            print("\n" + f"VERIFICATION: {verif_path.name}")
            print(sep)
            print(verif_path.read_text(encoding="utf-8", errors="replace").rstrip())
        else:
            print(f"{num:03d}: no verification file found")
        print()
    if failed or not found_any:
        raise AuditError("one or more requested records could not be shown", 1)


def _apply_transition_to_file(
    *,
    num: int,
    target_status: str,
    actor: str,
    fix_commit: Optional[str] = None,
    verified_commit: Optional[str] = None,
    verdict: Optional[str] = None,
    evidence: Sequence[str] = (),
    test: Optional[str] = None,
    changed: Sequence[str] = (),
    criteria: Sequence[str] = (),
    reason: Optional[str] = None,
) -> ItemResult:
    tid = f"{num:03d}"
    current = ""
    path = None
    try:
        ticket_path = _ticket_for(num)
        path = _verif_for(num, ticket_path)
        if path is None:
            return ItemResult(id=tid, ok=False, error="verification file not found")
        text = path.read_text(encoding="utf-8")
        current = _field(text, "Verification Status").upper() or "UNVERIFIED"
        _require_actor(actor, target_status)
        _validate_transition(current, target_status)
        new_resolution = target_status == "READY_FOR_VERIFICATION" and (
            current != target_status or bool(fix_commit and fix_commit != _field(text, "Fix Commit"))
        )
        if new_resolution:
            _check_resolution_eligibility(num)
        reopened = target_status == "OPEN" and current != "OPEN"
        regressed = target_status == "REGRESS" and current == "PASS"
        previous_revision = _field(text, "Verified Commit")
        new_revision = target_status in VERIFICATION_STATUSES and bool(
            verified_commit and verified_commit != previous_revision
        )
        if new_resolution or reopened or new_revision or regressed:
            text = _archive_verification(text, include_resolution=new_resolution or reopened)
        if reopened or new_resolution:
            for label in ("Fix Commit", "Resolved Date", "Resolved By"):
                text = _replace_field(text, label, "")

        today = date.today().isoformat()
        new = _set_ticket_field(text, "Original Severity", "Verification Status", target_status)
        if target_status == "READY_FOR_VERIFICATION":
            new = _set_ticket_field(new, "Verification Status", "Resolved Date", today)
            new = _set_ticket_field(new, "Resolved Date", "Resolved By", actor)
            if fix_commit is not None:
                new = _set_ticket_field(new, "Verified By", "Fix Commit", fix_commit)
            if evidence:
                new = _append_to_section(new, "## Resolution Evidence", _evidence_text(evidence))
            if changed:
                new = _append_to_section(new, "## Current State", "**File(s) Changed:**\n" + "\n".join(f"- `{x}`" for x in changed))
            if test is not None:
                new = _append_to_section(new, "## Test Verification", test)
            if verdict:
                new = _replace_section(new, "## Verdict", f"**{target_status}**\n\n{verdict}")
        elif target_status in VERIFICATION_STATUSES:
            if actor == "audit-verification":
                new = _set_ticket_field(new, "Resolved By", "Verified Date", today)
                new = _set_ticket_field(new, "Verified Date", "Verified By", actor)
            if verified_commit is not None:
                new = _set_ticket_field(new, "Fix Commit", "Verified Commit", verified_commit)
            if evidence:
                new = _append_to_section(new, "## Evidence", _evidence_text(evidence))
            if criteria:
                if ticket_path is None:
                    raise AuditError("criterion results require an existing ticket", 2)
                known = _acceptance_criteria(ticket_path.read_text(encoding="utf-8"))
                new = _append_criterion_results(new, criteria)
                for raw in criteria:
                    parsed = _criterion_result(raw)
                    if parsed and parsed[0] not in known:
                        raise AuditError(f"criterion {parsed[0]} is not defined in the ticket", 2)
            if test is not None:
                new = _append_to_section(new, "## Test Verification", test)
            verdict = verdict or reason
            if verdict:
                new = _replace_section(new, "## Verdict", f"**{target_status}**\n\n{verdict}")
            elif target_status in {"WONTFIX", "INVALID", "BLOCKED"} and current != target_status:
                raise AuditError(f"{target_status} requires a new --reason or --verdict", 2)
        elif target_status == "OPEN":
            if verdict:
                new = _replace_section(new, "## Verdict", f"**OPEN**\n\n{verdict}")

        # The exact same persisted representation is checked by doctor.
        _validate_transition_requirements(target_status, ticket_path, new)
        commit_value = verified_commit or fix_commit or ""
        new = _append_history(new, target_status, commit_value, actor, verdict or reason or "")
        _write_documents({path: new})
        return ItemResult(id=tid, ok=True, message=f"updated → {target_status}", path=_rel(path), status=target_status)
    except (AuditError, OSError, UnicodeError) as exc:
        message = exc.message if isinstance(exc, AuditError) else str(exc)
        return ItemResult(id=tid, ok=False, path=_rel(path) if path else "", status=current, error=message)


def _batch_transition(
    ids: Sequence[str],
    target_status: str,
    actor: str,
    *,
    fix_commit: Optional[str] = None,
    verified_commit: Optional[str] = None,
    verdict: Optional[str] = None,
    evidence: Sequence[str] = (),
    test: Optional[str] = None,
    changed: Sequence[str] = (),
    criteria: Sequence[str] = (),
    reason: Optional[str] = None,
    auto_commit: bool = False,
    allow_dirty: bool = False,
    commit_message: Optional[str] = None,
) -> BatchResult:
    status = target_status.upper()
    if status not in VALID_STATUSES:
        raise AuditError(f"invalid status '{target_status}'. Valid: {', '.join(sorted(VALID_STATUSES))}", 2)
    _require_actor(actor, status)
    if auto_commit:
        _ensure_clean_worktree(allow_dirty=allow_dirty)

    result = BatchResult(ok=True, status=status)
    changed_paths: list[Path] = []
    with _create_lock_cm():
        seen_ids: set[int] = set()
        for raw in ids:
            try:
                num = _parse_id(raw)
            except AuditError:
                item = ItemResult(id=raw, ok=False, error="invalid id")
                result.failed.append(item)
                continue
            if num in seen_ids:
                continue
            seen_ids.add(num)
            item = _apply_transition_to_file(
                num=num,
                target_status=status,
                actor=actor,
                fix_commit=fix_commit,
                verified_commit=verified_commit,
                verdict=verdict,
                evidence=evidence,
                test=test,
                changed=changed,
                criteria=criteria,
                reason=reason,
            )
            if item.ok:
                result.updated.append(item)
                if item.path:
                    changed_paths.append(ROOT / item.path)
            else:
                result.failed.append(item)
    result.ok = not result.failed
    if auto_commit and changed_paths and not result.failed:
        try:
            sha = _git_commit(changed_paths, commit_message or f"docs: audit {status.lower()} {' '.join(ids)}", allow_dirty=allow_dirty)
        except (AuditError, OSError) as exc:
            result.ok = False
            result.commit_error = f"records updated, but {exc}"
        else:
            for item in result.updated:
                item.message += f"; committed {sha}"
    return result


def _render_batch_result(result: BatchResult, as_json: bool, verb: str) -> None:
    if as_json:
        _json_print(result.to_json())
        return
    for item in result.updated:
        print(f"{item.id}: {verb} → {item.status}  ({item.path})")
    for item in result.failed:
        print(f"{item.id}: ERROR — {item.error}", file=sys.stderr)
    if result.commit_error:
        print(f"ERROR — {result.commit_error}", file=sys.stderr)


def cmd_update(args: argparse.Namespace) -> None:
    result = _batch_transition(
        args.id,
        args.status,
        args.actor,
        fix_commit=args.fix_commit,
        verified_commit=getattr(args, "verified_commit", None),
        verdict=args.verdict,
        evidence=args.evidence or [],
        test=args.test,
        changed=args.changed or [],
        criteria=args.criterion or [],
        auto_commit=args.git_commit,
        allow_dirty=args.allow_dirty,
    )
    _render_batch_result(result, args.json, "updated")
    sys.exit(result.exit_code())


def cmd_open(args: argparse.Namespace) -> None:
    result = _batch_transition(args.id, "OPEN", args.actor, verdict=args.verdict, auto_commit=args.git_commit, allow_dirty=args.allow_dirty)
    _render_batch_result(result, args.json, "opened")
    sys.exit(result.exit_code())


def cmd_resolve(args: argparse.Namespace) -> None:
    result = _batch_transition(
        args.id,
        "READY_FOR_VERIFICATION",
        args.actor,
        fix_commit=args.fix_commit,
        verdict=args.verdict or "Implementation complete; awaiting independent verification",
        evidence=args.evidence or [],
        test=args.test,
        changed=args.changed or [],
        auto_commit=args.git_commit,
        allow_dirty=args.allow_dirty,
        commit_message=f"docs: audit resolve {' '.join(args.id)}",
    )
    _render_batch_result(result, args.json, "resolved")
    sys.exit(result.exit_code())


def cmd_verify(args: argparse.Namespace) -> None:
    status = args.status.upper()
    if status not in VERIFICATION_STATUSES:
        raise AuditError(f"'{args.status}' is not a verification status. Valid: {', '.join(sorted(VERIFICATION_STATUSES))}", 2)
    result = _batch_transition(
        args.id,
        status,
        args.actor,
        verified_commit=args.verified_commit,
        verdict=args.verdict,
        evidence=args.evidence or [],
        test=args.test,
        criteria=args.criterion or [],
        reason=args.reason,
        auto_commit=args.git_commit,
        allow_dirty=args.allow_dirty,
        commit_message=f"docs: audit verify {' '.join(args.id)} → {status}",
    )
    _render_batch_result(result, args.json, "verified")
    sys.exit(result.exit_code())


def cmd_close(args: argparse.Namespace) -> None:
    result = _batch_transition(args.id, "INVALID", args.actor, verdict=args.reason, reason=args.reason)
    _render_batch_result(result, False, "closed")
    sys.exit(result.exit_code())


def cmd_wontfix(args: argparse.Namespace) -> None:
    result = _batch_transition(args.id, "WONTFIX", args.actor, verdict=args.reason, reason=args.reason)
    _render_batch_result(result, False, "wontfix")
    sys.exit(result.exit_code())


def cmd_reopen(args: argparse.Namespace) -> None:
    result = _batch_transition(args.id, "OPEN", args.actor, verdict=args.reason or "Reopened")
    _render_batch_result(result, False, "reopened")
    sys.exit(result.exit_code())


def _dependency_issues(records: Sequence[dict[str, Any]]) -> list[str]:
    tickets = {r["id"]: r for r in records if r.get("path")}
    issues: list[str] = []
    graph = {tid: set(r.get("depends_on", [])) for tid, r in tickets.items()}
    for tid, record in tickets.items():
        for label, inverse in (("depends_on", "blocks"), ("blocks", "depends_on")):
            for ref in record.get(label, []):
                if not re.fullmatch(r"[0-9]+", ref) or int(ref) < 1:
                    issues.append(f"Ticket {tid} has invalid {label} ID {ref!r}")
                    continue
                if ref == tid:
                    issues.append(f"Ticket {tid} has a self dependency")
                other = tickets.get(ref)
                if other is None:
                    issues.append(f"Ticket {tid} {label} missing ticket {ref}")
                elif tid not in other.get(inverse, []):
                    issues.append(f"Dependency {tid} {label} {ref} is not recorded on both tickets; use doctor --fix")
                if label == "blocks" and other:
                    graph[ref].add(tid)
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as exc:
        issues.append("Dependency cycle detected: " + " -> ".join(exc.args[1]))
    return list(dict.fromkeys(issues))


def _check_resolution_eligibility(num: int) -> None:
    records = load_records()
    issues = _dependency_issues(records)
    if issues:
        raise AuditError("invalid dependency state: " + "; ".join(issues), 1)
    record = next((r for r in records if r.get("num") == num and r.get("path")), None)
    if record is None:
        raise AuditError(f"ticket {num:03d} not found", 1)
    if record.get("decision") != "FIX":
        raise AuditError(f"ticket {num:03d} Decision is {record.get('decision')!r}; triage it to FIX before resolving", 2)
    states = {r["id"]: r.get("status", "") for r in records}
    if _is_blocked(record, states):
        raise AuditError(f"ticket {num:03d} has dependencies that have not reached PASS", 2)


def _is_blocked(record: dict[str, Any], status_by_id: dict[str, str]) -> bool:
    for dep in record.get("depends_on", []):
        if status_by_id.get(dep) not in _PASS_LIKE:
            return True
    return False


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _related_resolution_tickets(top: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Offer nearby ready-to-fix tickets; never turn suggestions into implicit work."""
    group = top.get("fix_group") or ""
    module = top.get("module") or ""
    phase = top.get("phase") or ""
    related: list[dict[str, str]] = []
    for candidate in candidates:
        if candidate["id"] == top["id"]:
            continue
        if group and candidate.get("fix_group") == group:
            reason = "fix-group"
        elif (
            not group
            and not candidate.get("fix_group")
            and module not in {"", "?"}
            and candidate.get("module") == module
            and (not phase or not candidate.get("phase") or candidate.get("phase") == phase)
        ):
            reason = "same-module"
        else:
            continue
        related.append({
            "id": candidate["id"],
            "title": candidate["title"],
            "module": candidate.get("module", ""),
            "p_level": candidate.get("p_level", ""),
            "reason": reason,
        })
    return related


def cmd_next(args: argparse.Namespace) -> None:
    records = load_records()
    issues = _dependency_issues(records)
    if issues:
        raise AuditError("invalid dependency state: " + "; ".join(issues), 1)
    status_by_id = {r["id"]: r.get("status", "") for r in records}
    if args.for_role == "resolution":
        allowed = {"OPEN", "PARTIAL", "FAIL", "REGRESS"}
    elif args.for_role == "verification":
        allowed = {"READY_FOR_VERIFICATION"}
    else:
        raise AuditError(f"unknown --for '{args.for_role}'. Use: resolution, verification", 2)

    candidates = []
    blocked_skipped = 0
    for r in records:
        status = r.get("status")
        if status not in allowed or not r.get("path") or not r.get("verification_path"):
            continue
        if args.category and r.get("category") != args.category.upper():
            continue
        if args.severity and str(r.get("severity", "")).lower() != args.severity.lower():
            continue
        if args.for_role == "resolution":
            if r.get("decision") not in TRIAGE_DECISIONS:
                raise AuditError(f"ticket {r['id']} has invalid or missing Decision; run triage set", 1)
            if r.get("decision") != "FIX":
                continue
        _validate_transition_requirements(status, Path(r["path"]), Path(r["verification_path"]).read_text(encoding="utf-8"))
        blocked = _is_blocked(r, status_by_id)
        if blocked and args.for_role == "resolution":
            blocked_skipped += 1
            continue
        candidates.append(r)

    if not candidates:
        payload = {
            "ok": True, "for": args.for_role, "ticket": None, "queue_size": 0,
            "blocked_skipped": blocked_skipped, "related_tickets": [],
        }
        if getattr(args, "json", False):
            _json_print(payload)
        else:
            suffix = f" ({blocked_skipped} blocked by dependencies)" if blocked_skipped else ""
            print(f"No tickets available for {args.for_role}.{suffix}")
        return

    def sort_key(r: dict[str, Any]) -> tuple[int, int, int, int]:
        plevel = _PLEVEL_ORDER.get(str(r.get("p_level", "")).upper(), 4)
        score = -_int_or_default(r.get("priority"), 0)
        sev = _SEVERITY_ORDER.get(str(r.get("severity", "?")).lower(), 4)
        num = _int_or_default(r.get("num"), 999999)
        return (plevel, score, sev, num)

    candidates.sort(key=sort_key)
    top = candidates[0]
    related = _related_resolution_tickets(top, candidates) if args.for_role == "resolution" else []
    if getattr(args, "json", False):
        _json_print({
            "ok": True,
            "for": args.for_role,
            "ticket": top,
            "queue_size": len(candidates),
            "blocked_skipped": blocked_skipped,
            "related_tickets": related,
        })
        return
    print(
        f"{top['id']}  [{top.get('severity', '?')}] [{top.get('status', '?')}] "
        f"[{top.get('p_level', '') or 'P?'} score={top.get('priority', '') or '?'}] {top.get('title', '')}"
    )
    if top.get("depends_on"):
        print(f"Depends on: {', '.join(top['depends_on'])}")
    if related:
        print("Related FIX tickets available for the same edit session:")
        for candidate in related:
            print(f"  {candidate['id']} [{candidate['p_level'] or 'P?'}] {candidate['title']} ({candidate['reason']})")
    if len(candidates) > 1:
        print(f"({len(candidates) - 1} more ticket(s) in queue)")


def _one_sided_dependency_edges() -> list[tuple[str, str]]:
    """Return (blocker, blocked) edges recorded on only one of the two tickets."""
    tickets: dict[str, dict[str, Any]] = {}
    for p in _all_ticket_files():
        t = parse_ticket(p)
        if t["num"] is not None:
            tickets.setdefault(t["id"], t)
    edges: set[tuple[str, str]] = set()
    for tid, t in tickets.items():
        for blocked in t["blocks"]:
            other = tickets.get(blocked)
            if other is not None and tid not in other["depends_on"]:
                edges.add((tid, blocked))
        for blocker in t["depends_on"]:
            other = tickets.get(blocker)
            if other is not None and tid not in other["blocks"]:
                edges.add((blocker, tid))
    return sorted(edges)


def _doctor_findings() -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    if not TICKETS_DIR.is_dir() or not VERIF_DIR.is_dir():
        issues.append("Audit workflow is not initialized. Use audit_init or the bundled CLI init command")
        return issues, warnings

    ticket_paths = list(_all_ticket_files())
    verif_paths = list(_named_verif_files())
    ticket_by_num: dict[int, Path] = {}
    verif_by_num: dict[int, Path] = {}

    for p in ticket_paths:
        num = _ticket_num(p.name)
        if num is not None:
            if num in ticket_by_num:
                issues.append(f"Duplicate ticket number {num:03d}: {p.name} and {ticket_by_num[num].name}")
            else:
                ticket_by_num[num] = p

    for p in verif_paths:
        num, category, _ = parse_ticket_filename(p.name)
        if num is None or num < 1 or category not in VALID_CATEGORIES:
            issues.append(f"Invalid verification filename: {p.name}; use NNN-CATEGORY-slug.md")
        if num is not None:
            if num in verif_by_num:
                issues.append(f"Duplicate verification number {num:03d}: {p.name} and {verif_by_num[num].name}")
            else:
                verif_by_num[num] = p

    for num, p in ticket_by_num.items():
        if num not in verif_by_num:
            issues.append(f"Ticket {num:03d} missing verification file: {p.name}")
        elif verif_by_num[num].name != p.name:
            issues.append(f"Ticket/verification name mismatch {num:03d}: {p.name} vs {verif_by_num[num].name}")

    for num, p in verif_by_num.items():
        if num not in ticket_by_num:
            issues.append(f"Orphan verification file {num:03d}: {p.name}")

    for p in ticket_paths:
        t = parse_ticket(p)
        if t["num"] is None or t["num"] < 1 or t["category"] not in VALID_CATEGORIES:
            issues.append(f"Invalid ticket filename: {p.name}; use NNN-CATEGORY-slug.md")
        if t["category"] not in VALID_CATEGORIES:
            issues.append(f"Invalid category in {p.name}: {t['category']}")
        if t["severity"] not in VALID_SEVERITIES:
            issues.append(f"Invalid severity in {p.name}: {t['severity']}")
        if t["decision"] not in TRIAGE_DECISIONS:
            issues.append(f"Invalid or missing Decision in {p.name}: {t['decision']!r}")
        if t["p_level"] and t["p_level"] not in {"P0", "P1", "P2", "P3"}:
            issues.append(f"Invalid P-level in {p.name}: {t['p_level']}")
        group = t["fix_group"]
        if group and not FIX_GROUP_PATTERN.fullmatch(group):
            issues.append(f"Invalid Fix Group in {p.name}: {group!r}")
        impact, effort = t["impact"], t["effort"]
        if impact and not re.fullmatch(r"[1-5]", impact):
            issues.append(f"Invalid Impact in {p.name}: {impact!r}")
        if effort and not re.fullmatch(r"[1-5]", effort):
            issues.append(f"Invalid Effort in {p.name}: {effort!r}")
        if re.fullmatch(r"[1-5]", impact) and re.fullmatch(r"[1-5]", effort):
            expected_priority = int(impact) * (6 - int(effort))
            if t["priority"] != str(expected_priority):
                issues.append(f"Inconsistent Priority in {p.name}: expected {expected_priority}, got {t['priority']!r}")
        elif t["priority"]:
            issues.append(f"Priority in {p.name} requires both Impact and Effort")

    for p in verif_paths:
        v = parse_verification(p)
        status = v["status"]
        if status not in VALID_STATUSES:
            issues.append(f"Invalid or missing Verification Status in {p.name}: {status}")
            continue
        ticket_path = ticket_by_num.get(v["num"])
        if status == "DRAFT":
            warnings.append(f"DRAFT ticket {p.name} is excluded from resolution queue")
        elif ticket_path:
            try:
                _validate_transition_requirements(status, ticket_path, v["_text"])
            except AuditError as exc:
                issues.append(f"{p.name}: {exc.message}")

    try:
        records = load_records()
    except AuditError as exc:
        issues.append(exc.message)
        return list(dict.fromkeys(issues)), warnings
    issues.extend(_dependency_issues(records))
    status_by_id = {r["id"]: r.get("status", "") for r in records}
    for record in records:
        for dep in record.get("depends_on", []):
            if status_by_id.get(dep) in {"FAIL", "BLOCKED", "WONTFIX", "INVALID"}:
                warnings.append(f"Ticket {record['id']} waits for {dep} ({status_by_id[dep]}); only PASS unblocks it")

    return issues, warnings


def cmd_doctor(args: argparse.Namespace) -> None:
    if args.fix:
        fixed: list[str] = []
        with _create_lock_cm():
            if not TICKETS_DIR.is_dir() or not VERIF_DIR.is_dir():
                result = _initialize_audit_tree(write_docs=True)
                if result["created_dirs"] or result["created_files"]:
                    fixed.append("initialized missing audit workflow directories/files")
            pending: dict[Path, str] = {}
            for path in _all_ticket_files():
                num, category, _ = parse_ticket_filename(path.name)
                if num is None or num < 1 or category not in VALID_CATEGORIES:
                    continue
                try:
                    ticket = _ticket_for(num)
                    verification = _verif_for(num, ticket)
                except AuditError:
                    continue  # Ambiguous records require explicit human repair, not another copy.
                if verification is None:
                    t = parse_ticket(path)
                    state = "OPEN" if _ticket_ready_for_open(t["_text"])[0] else "DRAFT"
                    pending[VERIF_DIR / path.name] = _verification_text(num, t["category"], t["severity"], t["slug"], state)
                    fixed.append(f"created verification stub for {num:03d}")
            for blocker, blocked in _one_sided_dependency_edges():
                try:
                    left = _ticket_for(_parse_id(blocker))
                    right = _ticket_for(_parse_id(blocked))
                    if left is None or right is None:
                        continue
                    for path, label, value in ((left, "Blocks", blocked), (right, "Depends On", blocker)):
                        text = pending[path] if path in pending else path.read_text(encoding="utf-8")
                        depends, blocks = set(_split_ids(_field(text, "Depends On"))), set(_split_ids(_field(text, "Blocks")))
                        (depends if label == "Depends On" else blocks).add(value)
                        pending[path] = _updated_dependency_text(depends, blocks, text)
                except AuditError:
                    continue
                fixed.append(f"recorded both sides of dependency {blocker} blocks {blocked}")
            _write_documents(pending)
        for item in fixed:
            print(f"FIXED: {item}")

    issues, warnings = _doctor_findings()
    if issues:
        print(f"Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  - {warning}")
        sys.exit(1)
    print("Audit directory is healthy.")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")


def cmd_export(args: argparse.Namespace) -> None:
    items = load_records()
    if args.json:
        _json_print(items)
        return
    if not items:
        print("No tickets found.")
        return
    print(f"{'ID':<6} {'Category':<14} {'Severity':<8} {'Status':<22} {'P':<3} Title")
    print("-" * 90)
    for it in items:
        print(
            f"{it.get('id', '???'):<6} {it.get('category', '?'):<14} {it.get('severity', '?'):<8} "
            f"{it.get('status', '?'):<22} {it.get('p_level', ''):<3} {str(it.get('title', ''))[:40]}"
        )


def _first_evidence_line(text: str) -> str:
    content = _section_content(text, "## Evidence")
    for line in content.splitlines():
        line = _PLACEHOLDER_RE.sub("", line).strip()
        if line:
            return line
    return ""


def _title_similarity(a: str, b: str) -> float:
    words_a = set(re.sub(r"[^\w\s]", "", a.lower()).split())
    words_b = set(re.sub(r"[^\w\s]", "", b.lower()).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def cmd_dedupe(args: argparse.Namespace) -> None:
    ticket_paths = list(_all_ticket_files())
    if len(ticket_paths) < 2:
        print("Need at least 2 tickets to dedupe.")
        return
    states = {record["id"]: record.get("status") for record in load_records()}
    tickets = []
    for path in ticket_paths:
        t = parse_ticket(path)
        if states.get(t["id"]) in {"INVALID", "WONTFIX"}:
            continue
        t["_evidence_first"] = _first_evidence_line(t["_text"])
        tickets.append(t)
    candidates = []
    for i, a in enumerate(tickets):
        for b in tickets[i + 1:]:
            if a["num"] is None or b["num"] is None:
                continue
            if a["category"] != b["category"] or a["module"] != b["module"]:
                continue
            title_sim = _title_similarity(a["title"], b["title"])
            evidence_match = a["_evidence_first"] and a["_evidence_first"] == b["_evidence_first"]
            score = min(1.0, title_sim + (0.3 if evidence_match else 0.0))
            if score >= 0.5:
                target = min(a["num"], b["num"])
                other = max(a["num"], b["num"])
                candidates.append({
                    "a_num": a["num"], "b_num": b["num"], "score": score,
                    "reason": "same module, same evidence" if evidence_match else "same module, similar title",
                    "recommendation": f"merge into {target:03d}", "other": other, "target": target,
                })
    if not candidates:
        print("No duplicate candidates found.")
        return
    candidates.sort(key=lambda c: -c["score"])
    if args.apply:
        if not args.actor:
            raise AuditError("--as is required when --apply modifies ticket status", 2)
        _require_actor(args.actor, "INVALID")
        planned: dict[int, int] = {}
        for candidate in sorted(candidates, key=lambda c: (c["other"], c["target"], -c["score"])):
            duplicate, target = candidate["other"], candidate["target"]
            if duplicate in planned or target in planned:
                continue
            if "INVALID" in ALLOWED_TRANSITIONS.get(states.get(f"{duplicate:03d}", ""), set()):
                planned[duplicate] = target
        for duplicate, target in planned.items():
            result = _batch_transition(
                [str(duplicate)], "INVALID", args.actor,
                verdict=f"Duplicate of {target:03d}: same module and matching finding",
            )
            if result.failed:
                _render_batch_result(result, False, "closed")
                sys.exit(result.exit_code())
        print(f"Marked {len(planned)} ticket(s) as INVALID (duplicate).")

    else:
        print("| Candidate | Similar To | Score | Reason | Recommendation |")
        print("|---|---|---|---|---|")
        for c in candidates:
            print(f"| {c['a_num']:03d} | {c['b_num']:03d} | {c['score']:.2f} | {md_cell(c['reason'])} | {md_cell(c['recommendation'])} |")
        print(f"\n{len(candidates)} candidate(s). Use --apply --as audit-verification to mark duplicates as INVALID.")


def cmd_baseline(args: argparse.Namespace) -> None:
    baselines_dir = ROOT / "audit" / "baselines"
    if args.tag is not None and (
        not args.tag.strip() or args.tag in {".", ".."} or "/" in args.tag or "\\" in args.tag
    ):
        raise AuditError("--tag must be a nonempty baseline name, not a path", 2)

    def read_baseline(path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("tickets"), dict):
                raise ValueError("expected an object with a tickets mapping")
            if not isinstance(data.get("created_at"), str):
                raise ValueError("created_at is missing")
            datetime.fromisoformat(data["created_at"])
            if any(not isinstance(record, dict) for record in data["tickets"].values()):
                raise ValueError("each ticket snapshot must be an object")
            return data
        except (OSError, UnicodeError, ValueError) as exc:
            raise AuditError(f"invalid baseline {path.name}: {exc}", 1) from exc

    # One field set drives both persisted snapshots and semantic comparison.
    # It includes every ticket field used by triage and resolution scheduling.
    semantic_defaults = {
        "category": "?", "severity": "?", "title": "", "module": "",
        "depends_on": [], "blocks": [],
        "impact": "", "effort": "", "priority": "", "p_level": "",
        "decision": "", "phase": "", "fix_group": "",
    }

    def snapshot() -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for r in load_records():
            if r.get("num") is None:
                continue
            out[r["id"]] = {
                "status": r.get("status", "UNVERIFIED"),
                **{field: r.get(field, default) for field, default in semantic_defaults.items()},
                "ticket_hash": r.get("ticket_hash", ""),
                "verification_hash": r.get("verification_hash", ""),
            }
        return out

    if args.action == "create":
        snap = snapshot()
        name = args.tag if args.tag is not None else datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")
        path = baselines_dir / f"{name}.json"
        if path.exists():
            raise AuditError(f"baseline {name!r} already exists; choose a new --tag", 1)
        baselines_dir.mkdir(parents=True, exist_ok=True)
        _write_documents({path: json.dumps({"created_at": datetime.now().isoformat(), "tickets": snap}, ensure_ascii=False, indent=2)})
        print(f"Baseline saved: {_rel(path)}")
        print(f"Tickets: {len(snap)}")
        return

    if args.tag:
        baseline_path = baselines_dir / f"{args.tag}.json"
    else:
        baselines = list(baselines_dir.glob("*.json"))
        if not baselines:
            raise AuditError("No baselines found. Run 'audit baseline create' first.", 1)
        baseline_path = max(
            baselines,
            key=lambda path: (datetime.fromisoformat(read_baseline(path)["created_at"]).timestamp(), path.name),
        )
    if not baseline_path.exists():
        raise AuditError(f"Baseline not found: {baseline_path}", 1)
    baseline = read_baseline(baseline_path)
    old = baseline.get("tickets", {})
    current = snapshot()
    new_ids = set(current) - set(old)
    removed_ids = set(old) - set(current)
    changed_status = []
    changed_content = []
    changed_semantic = []
    for tid in sorted(set(current) & set(old)):
        o = old[tid]
        n = current[tid]
        if o.get("status") != n.get("status"):
            changed_status.append({"id": tid, "from": o.get("status"), "to": n.get("status")})
        if o.get("ticket_hash") != n.get("ticket_hash") or o.get("verification_hash") != n.get("verification_hash"):
            changed_content.append(tid)
        for key in semantic_defaults:
            if o.get(key) != n.get(key):
                changed_semantic.append({"id": tid, "field": key, "from": o.get(key), "to": n.get(key)})
    print(f"Baseline: {baseline_path.name} ({baseline.get('created_at', 'unknown')})\n")
    print("| Metric | Count |")
    print("|---|---|")
    print(f"| New tickets | {len(new_ids)} |")
    print(f"| Removed tickets | {len(removed_ids)} |")
    print(f"| Changed status | {len(changed_status)} |")
    print(f"| Changed content hash | {len(changed_content)} |")
    print(f"| Changed semantic fields | {len(changed_semantic)} |")
    if new_ids:
        print(f"\n**New:** {', '.join(sorted(new_ids))}")
    if removed_ids:
        print(f"**Removed:** {', '.join(sorted(removed_ids))}")
    if changed_status:
        print("\n**Changed status:**")
        for c in changed_status:
            print(f"  {c['id']}: {c['from']} → {c['to']}")
    if changed_content:
        print(f"\n**Changed content:** {', '.join(sorted(changed_content))}")
    if changed_semantic:
        print("\n**Changed semantic fields:**")
        for c in changed_semantic:
            print(f"  {c['id']} {c['field']}: {c['from']} → {c['to']}")


def cmd_triage_set(args: argparse.Namespace) -> None:
    num = _parse_id(args.id)
    path = _ticket_for(num)
    if not path:
        raise AuditError(f"ticket {num:03d} not found", 1)
    if all(getattr(args, name) is None for name in ("impact", "effort", "p_level", "decision", "phase", "fix_group")):
        raise AuditError("triage set requires at least one field to update", 2)
    if args.fix_group and args.fix_group.lower() != "none" and not FIX_GROUP_PATTERN.fullmatch(args.fix_group):
        raise AuditError("--fix-group must be an alphanumeric slug (letters, numbers, ., _, -) or 'none'", 2)
    with _create_lock_cm():
        text = path.read_text(encoding="utf-8", errors="replace")
        if args.impact is not None:
            text = _set_ticket_field(text, "Blocks", "Impact", str(args.impact))
        if args.effort is not None:
            text = _set_ticket_field(text, "Impact", "Effort", str(args.effort))
        if args.impact is not None or args.effort is not None:
            impact = _int_or_default(_field(text, "Impact"), 0)
            effort = _int_or_default(_field(text, "Effort"), 0)
            if 1 <= impact <= 5 and 1 <= effort <= 5:
                priority = impact * (6 - effort)
                text = _set_ticket_field(text, "Effort", "Priority", str(priority))
                plevel = "P0" if priority >= 20 else "P1" if priority >= 12 else "P2" if priority >= 6 else "P3"
                text = _set_ticket_field(text, "Priority", "P-level", plevel)
            else:
                # An incomplete score has no computed Priority, but an explicitly
                # selected P-level is still meaningful for scheduling.
                text = _set_ticket_field(text, "Effort", "Priority", "")
        if args.p_level:
            text = _set_ticket_field(text, "Priority", "P-level", args.p_level)
        if args.decision:
            text = _set_ticket_field(text, "P-level", "Decision", args.decision)
        if args.phase is not None:
            text = _set_ticket_field(text, "Decision", "Phase", args.phase)
        if args.fix_group is not None:
            group = "" if args.fix_group.lower() == "none" else args.fix_group
            text = _set_ticket_field(text, "Phase", "Fix Group", group)
        _write_documents({path: text})
    print(f"{num:03d}: triage metadata updated ({_rel(path)})")


def _dependency_state(path: Path) -> tuple[set[str], set[str], str]:
    content = path.read_text(encoding="utf-8", errors="replace")
    return set(_split_ids(_field(content, "Depends On"))), set(_split_ids(_field(content, "Blocks"))), content


def _updated_dependency_text(depends: set[str], blocks: set[str], content: str) -> str:
    content = _set_ticket_field(content, "Source", "Depends On", _join_ids(sorted(depends)))
    return _set_ticket_field(content, "Depends On", "Blocks", _join_ids(sorted(blocks)))


def _mutate_dependencies(
    ticket_id: str, *, depends_on: Sequence[str], blocks: Sequence[str], remove: bool,
    pending: Optional[dict[Path, str]] = None,
) -> list[Path]:
    num = _parse_id(ticket_id)
    pending = dict(pending or {})
    source_path = next(
        (p for p in pending if p.parent == TICKETS_DIR and _ticket_num(p.name) == num),
        None,
    ) or _ticket_for(num)
    if source_path is None:
        raise AuditError(f"ticket {num:03d} not found", 1)
    source_id = f"{num:03d}"
    dep_ids = {_canonical_ticket_id(x) for x in depends_on}
    block_ids = {_canonical_ticket_id(x) for x in blocks}
    if not remove and (source_id in dep_ids or source_id in block_ids):
        raise AuditError("a ticket cannot depend on or block itself", 2)
    paths = {source_id: source_path}
    for ref in sorted((dep_ids | block_ids) - {source_id}, key=int):
        ref_path = _ticket_for(_parse_id(ref))
        if ref_path is None:
            if remove:
                continue  # A dangling reference must be removable without recreating its target.
            raise AuditError(f"ticket {ref} not found", 1)
        paths[ref] = ref_path
    state = {}
    for tid, path in paths.items():
        text = pending[path] if path in pending else path.read_text(encoding="utf-8")
        state[tid] = (
            set(_split_ids(_field(text, "Depends On"))),
            set(_split_ids(_field(text, "Blocks"))),
            text,
        )
    source_depends, source_blocks, _ = state[source_id]
    op = set.discard if remove else set.add
    for dep in dep_ids:
        op(source_depends, dep)
        if dep in state:
            op(state[dep][1], source_id)
    for blocked in block_ids:
        op(source_blocks, blocked)
        if blocked in state:
            op(state[blocked][0], source_id)
    updates = {**pending, **{
        path: _updated_dependency_text(*state[tid]) for tid, path in paths.items()
    }}
    if not remove:
        prospective_paths = set(_all_ticket_files()) | {p for p in updates if p.parent == TICKETS_DIR}
        prospective = [parse_ticket(p, updates.get(p)) for p in sorted(prospective_paths)]
        issues = _dependency_issues(prospective)
        if issues:
            raise AuditError("dependency update rejected: " + "; ".join(issues), 2)
    _write_documents(updates)
    return list(updates)


def cmd_deps_add(args: argparse.Namespace) -> None:
    if not args.depends_on and not args.blocks:
        raise AuditError("deps add requires --depends-on and/or --blocks", 2)
    with _create_lock_cm():
        changed = _mutate_dependencies(args.id, depends_on=args.depends_on or [], blocks=args.blocks or [], remove=False)
    print(f"{_parse_id(args.id):03d}: dependencies updated ({', '.join(_rel(p) for p in changed)})")


def cmd_deps_remove(args: argparse.Namespace) -> None:
    if not args.depends_on and not args.blocks:
        raise AuditError("deps remove requires --depends-on and/or --blocks", 2)
    with _create_lock_cm():
        changed = _mutate_dependencies(args.id, depends_on=args.depends_on or [], blocks=args.blocks or [], remove=True)
    print(f"{_parse_id(args.id):03d}: dependencies removed ({', '.join(_rel(p) for p in changed)})")


# ──────────────────────────────────────────────────────────────────────────────
# CLI dispatch
# ──────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="audit", description="Project-agnostic audit ticket workflow manager.")
    parser.add_argument("--root", help="Project root directory (default: cwd or AUDIT_ROOT)")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    init = sub.add_parser("init", help="Initialize audit workflow directories and onboarding docs")
    init.add_argument("--json", action="store_true", help="Output JSON only")
    init.add_argument("--no-docs", action="store_true", help="Create directories only; skip README files")

    create = sub.add_parser("create", help="Create a ticket; incomplete tickets are DRAFT")
    create.add_argument("category", help="Ticket category")
    create.add_argument("--title", required=True, help="Ticket title")
    create.add_argument("--severity", required=True, help="Ticket severity")
    create.add_argument("--module", default="?", help="Affected module")
    create.add_argument("--lines", default="N/A", help="Affected line range")
    create.add_argument("--source", help="Evidence source")
    create.add_argument("--depends-on", action="append", help="Dependency ticket ID; repeatable")
    create.add_argument("--blocks", action="append", help="Blocked ticket ID; repeatable")
    create.add_argument("--description", help="Problem description")
    create.add_argument("--expected", help="Expected behavior")
    create.add_argument("--actual", help="Actual behavior")
    create.add_argument("--evidence", action="append", help="Concrete evidence; repeatable")
    create.add_argument("--recommendation", help="Recommended fix")
    create.add_argument("--acceptance-criterion", action="append", help="Acceptance criterion; repeatable")
    create.add_argument("--suggested-verification", help="Suggested independent verification")
    create.add_argument("--open", action="store_true", help="Fail unless ticket has enough content to start as OPEN")
    create.add_argument("--json", action="store_true", help="Output JSON only")

    list_p = sub.add_parser("list", help="List tickets")
    list_p.add_argument("--status", action="append", help="Filter by status; repeatable")
    list_p.add_argument("--category", help="Filter by category")
    list_p.add_argument("--severity", help="Filter by severity")
    list_p.add_argument("--unverified", action="store_true", help="Show DRAFT/OPEN/UNVERIFIED tickets")
    list_p.add_argument("--json", action="store_true", help="Output JSON")

    show = sub.add_parser("show", help="Show ticket + verification")
    show.add_argument("id", nargs="+", help="Ticket ID(s)")

    status = sub.add_parser("status", help="Show verification status")
    status.add_argument("id", nargs="+", help="Ticket ID(s)")
    status.add_argument("--json", action="store_true")

    summary = sub.add_parser("summary", help="Show status summary")
    summary.add_argument("--json", action="store_true")

    def add_mutation_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--as", dest="actor", required=True, help="Actor role")
        p.add_argument("--git-commit", action="store_true", help="Commit audit metadata changes")
        p.add_argument("--allow-dirty", action="store_true", help="Allow git commit with dirty worktree")
        p.add_argument("--json", action="store_true", help="Output JSON only")

    update = sub.add_parser("update", help="Low-level status update with state/role enforcement")
    update.add_argument("id", nargs="+", help="Ticket ID(s)")
    update.add_argument("--status", required=True, help="New status")
    update.add_argument("--fix-commit", help="Fix commit SHA")
    update.add_argument("--verified-commit", help="Verified commit SHA")
    update.add_argument("--verdict", help="Verdict text")
    update.add_argument("--evidence", action="append", help="Evidence line; repeatable")
    update.add_argument("--test", help="Test command/result")
    update.add_argument("--changed", action="append", help="Changed file; repeatable")
    update.add_argument("--criterion", action="append", help="Criterion result, e.g. 'AC1: pass - pytest ...'; repeatable")
    add_mutation_common(update)

    open_p = sub.add_parser("open", help="Promote DRAFT ticket(s) to OPEN after evidence is complete")
    open_p.add_argument("id", nargs="+", help="Ticket ID(s)")
    open_p.add_argument("--verdict", default="Ticket accepted for resolution", help="Audit note")
    add_mutation_common(open_p)

    resolve = sub.add_parser("resolve", help="Mark implementation complete and ready for independent verification")
    resolve.add_argument("id", nargs="+", help="Ticket ID(s)")
    resolve.add_argument("--fix-commit", required=True, help="Implementation commit SHA")
    resolve.add_argument("--evidence", action="append", required=True, help="Resolution evidence; repeatable")
    resolve.add_argument("--test", required=True, help="Test command/result")
    resolve.add_argument("--changed", action="append", help="Changed file; repeatable")
    resolve.add_argument("--verdict", help="One-line resolution note")
    add_mutation_common(resolve)

    verify = sub.add_parser("verify", help="Assign independent verification status")
    verify.add_argument("id", nargs="+", help="Ticket ID(s)")
    verify.add_argument("--status", required=True, help="Verification status")
    verify.add_argument("--verified-commit", help="Commit SHA checked by verifier")
    verify.add_argument("--verdict", help="Verdict text")
    verify.add_argument("--reason", help="Rationale for WONTFIX/INVALID/BLOCKED")
    verify.add_argument("--evidence", action="append", help="Verification evidence; repeatable")
    verify.add_argument("--test", help="Test command/result")
    verify.add_argument("--criterion", action="append", help="Criterion result, e.g. 'AC1: pass - pytest ...'; repeatable")
    add_mutation_common(verify)

    next_p = sub.add_parser("next", help="Find next ticket for resolution or verification")
    next_p.add_argument("--for", dest="for_role", default="resolution", choices=["resolution", "verification"])
    next_p.add_argument("--category")
    next_p.add_argument("--severity")
    next_p.add_argument("--json", action="store_true", help="Output selected ticket as JSON")

    doctor = sub.add_parser("doctor", help="Check audit directory health")
    doctor.add_argument("--fix", action="store_true", help="Auto-fix missing verification stubs")

    export = sub.add_parser("export", help="Export canonical ticket records")
    export.add_argument("--json", action="store_true")

    close = sub.add_parser("close", help="Close ticket(s) as INVALID")
    close.add_argument("id", nargs="+")
    close.add_argument("--reason", required=True)
    close.add_argument("--as", dest="actor", required=True)

    wontfix = sub.add_parser("wontfix", help="Mark ticket(s) as WONTFIX")
    wontfix.add_argument("id", nargs="+")
    wontfix.add_argument("--reason", required=True)
    wontfix.add_argument("--as", dest="actor", required=True)

    reopen = sub.add_parser("reopen", help="Reopen ticket(s) to OPEN")
    reopen.add_argument("id", nargs="+")
    reopen.add_argument("--reason")
    reopen.add_argument("--as", dest="actor", required=True)

    dedupe = sub.add_parser("dedupe", help="Detect duplicate tickets")
    dedupe.add_argument("--apply", action="store_true", help="Mark duplicates as INVALID")
    dedupe.add_argument("--as", dest="actor", default="", help="Required with --apply")

    baseline = sub.add_parser("baseline", help="Create or compare audit baselines")
    baseline.add_argument("action", choices=["create", "compare"])
    baseline.add_argument("--tag")

    triage = sub.add_parser("triage", help="Manage executable triage metadata")
    triage_sub = triage.add_subparsers(dest="triage_command")
    triage_set = triage_sub.add_parser("set", help="Set triage metadata on a ticket")
    triage_set.add_argument("id")
    triage_set.add_argument("--impact", type=int, choices=range(1, 6))
    triage_set.add_argument("--effort", type=int, choices=range(1, 6))
    triage_set.add_argument("--p-level", choices=["P0", "P1", "P2", "P3"])
    triage_set.add_argument("--decision", choices=["FIX", "DEFER", "WONTFIX", "DUPLICATE"])
    triage_set.add_argument("--phase")
    triage_set.add_argument("--fix-group", help="Shared fix batch ID, or 'none' to clear")

    deps = sub.add_parser("deps", help="Manage ticket dependencies")
    deps_sub = deps.add_subparsers(dest="deps_command")
    deps_add = deps_sub.add_parser("add", help="Add dependency edges to a ticket")
    deps_add.add_argument("id")
    deps_add.add_argument("--depends-on", action="append")
    deps_add.add_argument("--blocks", action="append")
    deps_remove = deps_sub.add_parser("remove", help="Remove dependency edges from a ticket")
    deps_remove.add_argument("id")
    deps_remove.add_argument("--depends-on", action="append")
    deps_remove.add_argument("--blocks", action="append")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    read_only = args.command in {"list", "show", "status", "summary", "next", "export", None}
    read_only |= args.command == "doctor" and not args.fix
    read_only |= args.command == "baseline" and args.action == "compare"
    read_only |= args.command == "dedupe" and not args.apply
    try:
        with _create_lock_cm(read_only=read_only):
            if args.command == "init":
                cmd_init(args)
            elif args.command == "create":
                cmd_create(args)
            elif args.command == "list":
                cmd_list(args)
            elif args.command == "show":
                cmd_show(args)
            elif args.command == "status":
                cmd_status(args)
            elif args.command == "summary":
                cmd_summary(args)
            elif args.command == "update":
                cmd_update(args)
            elif args.command == "open":
                cmd_open(args)
            elif args.command == "resolve":
                cmd_resolve(args)
            elif args.command == "verify":
                cmd_verify(args)
            elif args.command == "next":
                cmd_next(args)
            elif args.command == "doctor":
                cmd_doctor(args)
            elif args.command == "export":
                cmd_export(args)
            elif args.command == "close":
                cmd_close(args)
            elif args.command == "wontfix":
                cmd_wontfix(args)
            elif args.command == "reopen":
                cmd_reopen(args)
            elif args.command == "dedupe":
                cmd_dedupe(args)
            elif args.command == "baseline":
                cmd_baseline(args)
            elif args.command == "triage" and args.triage_command == "set":
                cmd_triage_set(args)
            elif args.command == "deps" and args.deps_command == "add":
                cmd_deps_add(args)
            elif args.command == "deps" and args.deps_command == "remove":
                cmd_deps_remove(args)
            else:
                parser.print_help()
                sys.exit(1)
    except AuditError as exc:
        print(f"Error: {exc.message}", file=sys.stderr)
        sys.exit(exc.code)
    except (OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
