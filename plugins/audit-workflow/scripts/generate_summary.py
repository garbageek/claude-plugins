#!/usr/bin/env python3
"""
Generate audit summary statistics from ticket records.

Prefer the canonical `audit export --json` model when the CLI is available;
fall back to parsing ticket Markdown files directly for compatibility.

Usage:
    python generate_summary.py /path/to/audit/tickets
    python generate_summary.py /path/to/audit/tickets --write
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Optional

from audit_lib import VALID_CATEGORIES, md_cell, parse_ticket_filename


def _project_root_from_tickets_dir(tickets_dir: Path) -> Path | None:
    resolved = tickets_dir.resolve()
    if resolved.name == "tickets" and resolved.parent.name == "audit":
        return resolved.parent.parent
    return None


def _canonical_records(tickets_dir: Path) -> list[dict[str, Any]] | None:
    """Read canonical records through `audit export --json` if possible."""
    root = _project_root_from_tickets_dir(tickets_dir)
    audit_cli = Path(__file__).resolve().parents[1] / "bin" / "audit"
    if root is None or not audit_cli.exists():
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
    return [r for r in data if isinstance(r, dict) and r.get("path")]


def parse_ticket(filepath: Path) -> Optional[dict[str, Any]]:
    """Fallback Markdown parser for ticket summary fields."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"Warning: cannot read {filepath}: {exc}", file=sys.stderr)
        return None

    ticket_num, category, slug = parse_ticket_filename(filepath.name)
    if category == "?":
        return None

    severity = "unknown"
    for pattern in [
        r"\*\*Severity:\*\*\s*`(\w+)`",
        r"^##\s*Severity:\s*(\w+)",
    ]:
        severity_match = re.search(pattern, content, re.MULTILINE)
        if severity_match:
            severity = severity_match.group(1)
            break

    module = "N/A"
    for pattern in [
        r"\*\*Target Module:\*\*\s*`([^`]+)`",
        r"\*\*Module:\*\*\s*`([^`]+)`",
        r"\*\*Модуль:\*\*\s*`([^`]+)`",
    ]:
        module_match = re.search(pattern, content)
        if module_match:
            module = module_match.group(1)
            break

    top_module = module.split("/")[0] if module != "N/A" else "N/A"
    return {
        "number": ticket_num,
        "category": category.upper(),
        "slug": slug,
        "severity": severity.lower(),
        "module": top_module,
        "filepath": filepath,
    }


def _tickets_from_canonical_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tickets: list[dict[str, Any]] = []
    for record in records:
        category = str(record.get("category", "?")).upper()
        if category == "?":
            continue
        module = str(record.get("module") or "N/A")
        ticket_path = Path(str(record.get("path") or ""))
        slug = str(record.get("slug") or ticket_path.stem or record.get("title") or "ticket")
        tickets.append({
            "number": record.get("num") or record.get("id") or "?",
            "category": category,
            "slug": slug,
            "severity": str(record.get("severity") or "unknown").lower(),
            "module": module.split("/")[0] if module != "N/A" else "N/A",
            "filepath": ticket_path,
        })
    return tickets


def _load_tickets(tickets_dir: Path) -> list[dict[str, Any]]:
    records = _canonical_records(tickets_dir)
    if records is not None:
        return _tickets_from_canonical_records(records)
    tickets = []
    for f in sorted(tickets_dir.glob("*.md")):
        parsed = parse_ticket(f)
        if parsed:
            tickets.append(parsed)
    return tickets


def generate_summary(tickets_dir: Path) -> str:
    """Generate Markdown summary from canonical records or ticket files."""
    tickets = _load_tickets(tickets_dir)
    if not tickets:
        return "# Audit Summary\n\nNo tickets found."

    categories = sorted(VALID_CATEGORIES)
    severities = ["critical", "high", "medium", "low"]

    cat_sev: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    mod_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for t in tickets:
        cat_sev[str(t["category"])][str(t["severity"])] += 1
        mod_stats[str(t["module"])] ["total"] += 1
        mod_stats[str(t["module"])] [str(t["severity"])] += 1

    lines = [
        "# Audit Discovery Summary",
        "",
        f"**Date:** {date.today().isoformat()}",
        f"**Total Tickets:** {len(tickets)}",
        "**Source:** `audit export --json` when available, Markdown fallback otherwise",
        "",
        "---",
        "",
        "## By Category",
        "",
        "| Category | Critical | High | Medium | Low | Total |",
        "|----------|----------|------|--------|-----|-------|",
    ]

    totals: dict[str, int] = defaultdict(int)
    for cat in categories:
        row = [md_cell(cat)]
        cat_total = 0
        for sev in severities:
            count = cat_sev[cat][sev]
            row.append(str(count))
            totals[sev] += count
            cat_total += count
        row.append(str(cat_total))
        lines.append("| " + " | ".join(row) + " |")

    extra_cats = set(cat_sev.keys()) - set(categories)
    for cat in sorted(extra_cats):
        row = [md_cell(cat)]
        cat_total = 0
        for sev in severities:
            count = cat_sev[cat][sev]
            row.append(str(count))
            totals[sev] += count
            cat_total += count
        row.append(str(cat_total))
        lines.append("| " + " | ".join(row) + " |")

    total_row = ["**Total**"]
    grand_total = 0
    for sev in severities:
        total_row.append(str(totals[sev]))
        grand_total += totals[sev]
    total_row.append(str(grand_total))
    lines.append("| " + " | ".join(total_row) + " |")

    lines.extend([
        "",
        "---",
        "",
        "## By Module",
        "",
        "| Module | Tickets | Critical | High | Medium | Low |",
        "|--------|---------|----------|------|--------|-----|",
    ])

    for mod in sorted(mod_stats.keys()):
        stats = mod_stats[mod]
        row = [
            md_cell(mod),
            str(stats["total"]),
            str(stats.get("critical", 0)),
            str(stats.get("high", 0)),
            str(stats.get("medium", 0)),
            str(stats.get("low", 0)),
        ]
        lines.append("| " + " | ".join(row) + " |")

    critical_tickets = sorted(
        [t for t in tickets if t["severity"] == "critical"],
        key=lambda t: int(t["number"]) if str(t["number"]).isdigit() else 999999,
    )
    high_tickets = sorted(
        [t for t in tickets if t["severity"] == "high"],
        key=lambda t: int(t["number"]) if str(t["number"]).isdigit() else 999999,
    )

    if critical_tickets or high_tickets:
        lines.extend(["", "---", "", "## Priority Issues", ""])

        if critical_tickets:
            lines.extend(["### Critical", ""])
            for t in critical_tickets:
                lines.append(f"- **{md_cell(t['number'])}-{md_cell(t['category'])}-{md_cell(t['slug'])}** ({md_cell(t['module'])})")
            lines.append("")

        if high_tickets:
            lines.extend(["### High", ""])
            for t in high_tickets:
                lines.append(f"- **{md_cell(t['number'])}-{md_cell(t['category'])}-{md_cell(t['slug'])}** ({md_cell(t['module'])})")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python generate_summary.py /path/to/audit/tickets [--write]", file=sys.stderr)
        sys.exit(1)

    tickets_dir = Path(sys.argv[1])
    if not tickets_dir.is_dir():
        print(f"Error: {tickets_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    summary = generate_summary(tickets_dir)
    print(summary)

    if "--write" in sys.argv[2:]:
        summary_path = tickets_dir.parent / "SUMMARY.md"
        summary_path.write_text(summary, encoding="utf-8")
        print(f"\nWritten to {summary_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
