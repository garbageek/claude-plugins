#!/usr/bin/env python3
"""
Generate verification summary from audit verification records.

Prefer the canonical `audit export --json` model when the CLI is available;
fall back to parsing verification Markdown files directly for compatibility.

Usage:
    python generate_verification_report.py /path/to/audit/verification/details
    python generate_verification_report.py /path/to/audit/verification/details --write
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

SHARED_SCRIPTS_DIR = Path(__file__).resolve().parent
if SHARED_SCRIPTS_DIR.is_dir():
    sys.path.insert(0, str(SHARED_SCRIPTS_DIR))

try:
    from audit_lib import VALID_CATEGORIES, _field, md_cell
except ModuleNotFoundError:
    VALID_CATEGORIES = {
        "BUG", "DEGRADED", "LOST", "TODO", "TEST",
        "CONFIG", "SECURITY", "CODE-QUALITY",
    }

    def _field(text: str, label: str) -> str:
        pattern_strict = rf"\*\*{re.escape(label)}:\*\*\s+`([^`\n]*)`"
        m = re.search(pattern_strict, text)
        if m:
            return m.group(1).strip()
        pattern_fallback = rf"\*\*{re.escape(label)}:\*\*\s+([^\n]+)"
        m = re.search(pattern_fallback, text)
        if not m:
            return ""
        value = m.group(1).strip()
        if value == "``":
            return ""
        if value.startswith("`") and value.endswith("`"):
            return value[1:-1].strip()
        return value

    def md_cell(value: object) -> str:
        text = "" if value is None else str(value)
        return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


CANONICAL_STATUSES = [
    "DRAFT",
    "OPEN",
    "READY_FOR_VERIFICATION",
    "PASS",
    "PARTIAL",
    "FAIL",
    "REGRESS",
    "WONTFIX",
    "INVALID",
    "BLOCKED",
]


def _project_root_from_details_dir(details_dir: Path) -> Path | None:
    resolved = details_dir.resolve()
    if resolved.name == "details" and resolved.parent.name == "verification" and resolved.parent.parent.name == "audit":
        return resolved.parent.parent.parent
    return None


def _find_audit_cli(details_dir: Path) -> Path | None:
    candidates = [
        SHARED_SCRIPTS_DIR / "audit",
    ]
    root = _project_root_from_details_dir(details_dir)
    if root is not None:
        candidates.extend([
            root / "audit-cli",
            Path(__file__).resolve().parents[1] / "bin" / "audit",
        ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _canonical_records(details_dir: Path) -> list[dict[str, Any]] | None:
    root = _project_root_from_details_dir(details_dir)
    audit_cli = _find_audit_cli(details_dir)
    if root is None or audit_cli is None:
        return None
    try:
        result = subprocess.run(
            [sys.executable, str(audit_cli), "--root", str(root), "export", "--json"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    return [r for r in data if isinstance(r, dict) and r.get("verification_path")]


def _strip_verdict_status(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(
        r"^\*\*(?:DRAFT|PASS|PARTIAL|FAIL|REGRESS|WONTFIX|BLOCKED|INVALID|READY_FOR_VERIFICATION|OPEN)\*\*\s*",
        "",
        text,
    ).strip()
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _records_to_verifications(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append({
            "ticket_id": str(record.get("id") or record.get("num") or "???"),
            "status": str(record.get("status") or "UNKNOWN").upper(),
            "category": str(record.get("category") or "UNKNOWN").upper(),
            "severity": str(record.get("severity") or "unknown").lower(),
            "reason": _strip_verdict_status(str(record.get("verdict") or "")),
            "filepath": Path(str(record.get("verification_path") or "")),
        })
    return rows


def _section_content(text: str, section: str) -> str:
    m = re.search(rf"^{re.escape(section)}\s*$", text, flags=re.MULTILINE)
    if not m:
        return ""
    start = m.end()
    next_m = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
    end = start + next_m.start() if next_m else len(text)
    return text[start:end].strip()


def parse_verification(filepath: Path) -> dict[str, Any] | None:
    """Fallback parser for a single verification Markdown file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    ticket_id = filepath.stem

    status = _field(content, "Verification Status") or _field(content, "Status") or "UNKNOWN"
    category = _field(content, "Original Category")
    severity = _field(content, "Original Severity")

    if not category or not severity:
        tickets_dir = filepath.parents[2] / "tickets"
        ticket_path = tickets_dir / f"{ticket_id}.md"
        if ticket_path.exists():
            ticket_text = ticket_path.read_text(encoding="utf-8", errors="replace")
            category = category or _field(ticket_text, "Category")
            severity = severity or _field(ticket_text, "Severity")

    verdict_reason = _strip_verdict_status(_section_content(content, "## Verdict"))
    if not verdict_reason:
        verdict_match = re.search(
            r"^\*\*(?:DRAFT|PASS|PARTIAL|FAIL|REGRESS|WONTFIX|BLOCKED|INVALID|READY_FOR_VERIFICATION|OPEN)\*\*\s*(?:\n\n|\n)(.+?)(?:\n\n|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        )
        if verdict_match:
            verdict_reason = verdict_match.group(1).strip().split("\n")[0]

    return {
        "ticket_id": ticket_id,
        "status": status.upper(),
        "category": (category or "UNKNOWN").upper(),
        "severity": (severity or "unknown").lower(),
        "reason": verdict_reason,
        "filepath": filepath,
    }


def _load_verifications(details_dir: Path) -> list[dict[str, Any]]:
    records = _canonical_records(details_dir)
    if records is not None:
        return _records_to_verifications(records)
    verifications = []
    for f in details_dir.glob("*.md"):
        parsed = parse_verification(f)
        if parsed:
            verifications.append(parsed)
    return verifications


def generate_report(details_dir: Path) -> str:
    """Generate Markdown verification report from canonical records or detail files."""
    verifications = _load_verifications(details_dir)
    if not verifications:
        return "# Verification Report\n\nNo verification files found."

    status_counts: dict[str, int] = defaultdict(int)
    for v in verifications:
        status_counts[v["status"]] += 1

    total = len(verifications)
    categories = sorted(VALID_CATEGORIES)
    cat_status: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for v in verifications:
        cat_status[v["category"]][v["status"]] += 1
        cat_status[v["category"]]["total"] += 1

    lines = [
        "# Audit Verification Report",
        "",
        f"**Date:** {date.today().isoformat()}",
        f"**Tickets Reviewed:** {total}",
        "**Source:** `audit export --json` when available, Markdown fallback otherwise",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Status | Count | Percentage |",
        "|--------|-------|------------|",
    ]

    for status in CANONICAL_STATUSES:
        count = status_counts[status]
        pct = (count / total * 100) if total else 0
        lines.append(f"| {md_cell(status)} | {count} | {pct:.1f}% |")

    extra_statuses = set(status_counts.keys()) - set(CANONICAL_STATUSES)
    for status in sorted(extra_statuses):
        count = status_counts[status]
        pct = (count / total * 100) if total else 0
        lines.append(f"| {md_cell(status)} | {count} | {pct:.1f}% |")

    lines.extend([
        "",
        "---",
        "",
        "## By Original Category",
        "",
        "| Category | Total | Pass | Partial | Fail | Regress | Blocked |",
        "|----------|-------|------|---------|------|---------|---------|",
    ])

    for cat in categories:
        stats = cat_status[cat]
        if stats["total"] > 0:
            lines.append(
                f"| {md_cell(cat)} | {stats['total']} | {stats.get('PASS', 0)} | "
                f"{stats.get('PARTIAL', 0)} | {stats.get('FAIL', 0)} | "
                f"{stats.get('REGRESS', 0)} | {stats.get('BLOCKED', 0)} |"
            )

    extra_cats = set(cat_status.keys()) - set(categories)
    for cat in sorted(extra_cats):
        stats = cat_status[cat]
        if stats["total"] > 0:
            lines.append(
                f"| {md_cell(cat)} | {stats['total']} | {stats.get('PASS', 0)} | "
                f"{stats.get('PARTIAL', 0)} | {stats.get('FAIL', 0)} | "
                f"{stats.get('REGRESS', 0)} | {stats.get('BLOCKED', 0)} |"
            )

    def add_status_section(status: str, title: str, issue_header: str) -> None:
        rows = [v for v in verifications if v["status"] == status]
        if not rows:
            return
        lines.extend([
            "",
            "---",
            "",
            f"## {title}",
            "",
            f"| Ticket | Category | Severity | {issue_header} |",
            f"|--------|----------|----------|{'-' * (len(issue_header) + 2)}|",
        ])
        for v in rows:
            reason = v["reason"][:50] + "..." if len(v["reason"]) > 50 else v["reason"]
            lines.append(f"| {md_cell(v['ticket_id'])} | {md_cell(v['category'])} | {md_cell(v['severity'])} | {md_cell(reason)} |")

    add_status_section("FAIL", "Failed Tickets (Require Action)", "Issue")
    add_status_section("PARTIAL", "Partial Tickets (May Need Follow-up)", "Remaining")
    add_status_section("REGRESS", "Regressed Tickets (Were Fixed, Now Broken)", "Issue")
    add_status_section("BLOCKED", "Blocked Tickets", "Blocker")

    pass_count = status_counts["PASS"]
    pass_rate = (pass_count / total * 100) if total else 0

    lines.extend([
        "",
        "---",
        "",
        "## Metrics",
        "",
        f"- **Pass Rate:** {pass_rate:.1f}% ({pass_count}/{total})",
        f"- **Actionable:** {status_counts['FAIL'] + status_counts['PARTIAL'] + status_counts['REGRESS']} tickets need attention",
        f"- **Blocked:** {status_counts['BLOCKED']} tickets could not be verified",
        f"- **Open/Not Ready:** {status_counts['DRAFT'] + status_counts['OPEN'] + status_counts['READY_FOR_VERIFICATION']} tickets not fully verified",
    ])

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python generate_verification_report.py /path/to/audit/verification/details [--write]", file=sys.stderr)
        sys.exit(1)

    details_dir = Path(sys.argv[1])
    if not details_dir.is_dir():
        print(f"Error: {details_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    report = generate_report(details_dir)
    print(report)

    if len(sys.argv) > 2 and sys.argv[2] == "--write":
        report_path = details_dir.parent / f"{date.today().isoformat()}-verification.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\nWritten to {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
