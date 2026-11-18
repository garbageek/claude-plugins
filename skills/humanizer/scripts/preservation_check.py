#!/usr/bin/env python3
"""Read-only, conservative preservation checks for UTF-8 prose edits.

This is not an authorship detector or a semantic equivalence test. It reports
exact recognized-token occurrence changes and, optionally, edits outside
permitted ORIGINAL line ranges. No third-party packages or network access.

Exit codes: 0 = no mechanical issue; 1 = review differences; 2 = invalid input.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import difflib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

MAX_BYTES = 8 * 1024 * 1024
TokenCounts = Counter[tuple[str, str]]
TokenOffsets = dict[tuple[str, str], int]
Range = tuple[int, int]  # inclusive, one-based original lines
COMMON_CAPS = {"OK", "FYI", "ASAP", "AM", "PM", "TLDR", "PS"}


def decode_utf8(data: bytes, label: str) -> str:
    """Decode a bounded byte input without normalizing line endings."""
    if len(data) > MAX_BYTES:
        raise ValueError(f"Input exceeds the {MAX_BYTES}-byte limit: {label}")
    if b"\x00" in data:
        raise ValueError(f"NUL byte found; use a format-native document tool: {label}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Input is not valid UTF-8: {label}") from exc


def read_utf8(path: Path) -> str:
    """Read bytes without newline translation; reject binaries and large input."""
    if not path.is_file():
        raise ValueError(f"Not a regular readable file: {path}")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    return decode_utf8(data, str(path))


def block_spans(text: str) -> list[tuple[int, int, str]]:
    """Recognize initial frontmatter, fenced code, and explicit quote lines.

    Unclosed fences are protected to EOF. Indented code and lazy blockquotes
    require manual protection. This intentionally is not a Markdown parser.
    """
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    spans: list[tuple[int, int, str]] = []
    i = 0
    if lines and lines[0].lstrip("\ufeff").rstrip("\r\n") == "---":
        for j in range(1, len(lines)):
            if lines[j].rstrip("\r\n") in {"---", "..."}:
                spans.append((0, starts[j + 1], "frontmatter"))
                i = j + 1
                break
    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        if fence and not (fence[1][0] == "`" and "`" in fence[2]):
            marker = fence[1]
            close = re.compile(r"^ {0,3}" + re.escape(marker[0]) +
                               r"{" + str(len(marker)) + r",}[ \t]*(?:\r?\n|\r)?$")
            j = i + 1
            while j < len(lines) and not close.match(lines[j]):
                j += 1
            end = min(j + 1, len(lines))
            spans.append((starts[i], starts[end], "fenced_code"))
            i = end
        elif re.match(r"^ {0,3}>", line):
            spans.append((starts[i], starts[i + 1], "blockquote_line"))
            i += 1
        else:
            i += 1
    return spans


# Recognizers deliberately report candidates rather than parsing all languages.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("inline_code", re.compile(r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)")),
    ("math", re.compile(r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|"
                        r"(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$|"
                        r"(?<![\\$])\$(?!\$)[^\n$]+(?<!\\)\$(?!\$)")),
    ("quotation", re.compile(r'“[^”\n]*”|«[^»\n]*»|„[^“\n]*“|'
                             r'"(?:\\.|[^"\\\n])*"|(?<!\w)\x27[^\x27\n]+\x27(?!\w)')),
    ("url", re.compile(r'https?://[^\s<>"`]+')),
    ("citation", re.compile(r"\\cite[A-Za-z]*\*?(?:\[[^\]\n]*\]){0,2}\{[^}\n]+\}|"
                            r"\[(?:@[^\]\n]+|\^[^\]\n]+|\d+(?:\s*[-–,;]\s*\d+)*)\]")),
    ("reference_definition", re.compile(r"^ {0,3}\[[^\]\n]+\]:[^\r\n]*(?:\r?\n|\r|$)", re.M)),
    ("date", re.compile(r"(?<!\w)\d{4}-\d{2}-\d{2}(?!\w)|"
                        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                        r"[a-z]*\.? \d{1,2}\b", re.I)),
    ("version", re.compile(r"(?<!\w)v\d+(?:\.\d+)+(?:[-+][\w.-]+)?(?!\w)")),
    ("path", re.compile(r"(?<![\w:/])(?:~/|\./|\.\./|/[A-Za-z0-9_.-]|"
                        r"[A-Za-z]:\\|[A-Za-z0-9_.-]+/)[^\s<>\x27\"`]*")),
    ("identifier", re.compile(r"(?<!\w)(?:[A-Za-z_]\w*_\w+|"
                              r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+|"
                              r"[a-z]+(?:[A-Z][A-Za-z0-9]*)+|"
                              r"[A-Z][a-z]+[A-Z][A-Za-z0-9]*|"
                              r"[A-Z]{2,}[A-Z0-9_-]*|--[A-Za-z][\w-]*)(?!\w)")),
    ("number", re.compile(r"(?<![\w.])[+\-−]?(?:\d+(?:[.,]\d+|[ \u00a0\u202f]\d{3})*|\.\d+)"
                          r"(?:[eE][+\-]?\d+)?"
                          r"(?:[ \t\u00a0\u202f]?(?:%|°[CFK]|µs|μs|ms|ns|s|sec|min|h|hrs?|days?|"
                          r"minutes?|hours?|bytes?|KiB|MiB|GiB|KB|MB|GB|TB|"
                          r"Hz|kHz|MHz|GHz|mm|cm|km|m|kg|mg|g|k|K|M|x|×|USD|EUR|\$|credits?)"
                          r"(?!\w))?(?!\w)")),
)


def protected_counts(text: str, literals: Iterable[str] = (),
                     *, first_offsets: TokenOffsets | None = None) -> TokenCounts:
    counts: TokenCounts = Counter()
    masked = list(text)
    for start, end, kind in block_spans(text):
        key = (kind, text[start:end])
        counts[key] += 1
        if first_offsets is not None:
            first_offsets.setdefault(key, start)
        # Keep character offsets and line boundaries stable for all recognizers.
        for i in range(start, end):
            if masked[i] not in "\r\n":
                masked[i] = " "
    prose = "".join(masked)
    for kind, regex in PATTERNS:
        for match in regex.finditer(prose):
            value = match.group(0)
            if kind == "identifier" and value in COMMON_CAPS:
                continue
            # Keep URL candidates exact. Terminal punctuation can be part of
            # a query/path; guessing it away could hide a meaningful change.
            if value.strip():
                key = (kind, value)
                counts[key] += 1
                if first_offsets is not None:
                    first_offsets.setdefault(key, match.start())
    for literal in set(literals):
        if not literal:
            raise ValueError("Protected literals must not be empty")
        occurrences = text.count(literal)
        if occurrences:
            key = ("explicit_literal", literal)
            counts[key] = occurrences
            if first_offsets is not None:
                first_offsets[key] = text.find(literal)
    return counts


def parse_ranges(values: Iterable[str], line_count: int) -> list[Range]:
    ranges: list[Range] = []
    for value in values:
        match = re.fullmatch(r"([1-9]\d*):([1-9]\d*)", value)
        if not match:
            raise ValueError(f"Invalid range {value!r}; expected START:END")
        start, end = map(int, match.groups())
        if start > end or end > line_count:
            raise ValueError(f"Range {value!r} is outside the {line_count} original lines")
        ranges.append((start, end))
    return ranges


def scope_findings(source: str, draft: str, ranges: list[Range]) -> list[dict[str, Any]]:
    before, after = source.splitlines(keepends=True), draft.splitlines(keepends=True)
    permitted = {line for start, end in ranges for line in range(start, end + 1)}
    findings: list[dict[str, Any]] = []
    # Matching blocks are a diff alignment, not proof of edit intent in repeated text.
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=True)
    for kind, a, b, c, d in matcher.get_opcodes():
        if kind == "equal":
            continue
        if kind == "insert":
            neighbors = ([a] if a > 0 else []) + ([a + 1] if a < len(before) else [])
            allowed = bool(neighbors) and all(n in permitted for n in neighbors)
        else:
            allowed = all(n in permitted for n in range(a + 1, b + 1))
        if not allowed:
            findings.append({"kind": "edit_scope", "operation": kind,
                             "source_lines": [a + 1, b] if b > a else [],
                             "insert_after_source_line": a if kind == "insert" else None,
                             "draft_lines": [c + 1, d] if d > c else [],
                             "message": "Change reaches outside the permitted original lines"})
    return findings


def newline_types(text: str) -> list[str]:
    names = {"\n": "LF", "\r\n": "CRLF", "\r": "CR"}
    return sorted({names[m.group()] for m in re.finditer(r"\r\n|\r|\n", text)})


def line_starts(text: str) -> list[int]:
    """Index the beginning of every line once for efficient offset lookup."""
    starts = [0]
    starts.extend(match.end() for match in re.finditer(r"\r\n|\r|\n", text))
    return starts


def compare(source: str, draft: str, *, literals: Iterable[str] = (),
            ranges: list[Range] | None = None) -> dict[str, Any]:
    literals = tuple(literals)
    for literal in literals:
        if not literal or literal not in source:
            raise ValueError(f"Protected literal is empty or absent from source: {literal!r}")
    old_offsets: TokenOffsets = {}
    new_offsets: TokenOffsets = {}
    old = protected_counts(source, literals, first_offsets=old_offsets)
    new = protected_counts(draft, literals, first_offsets=new_offsets)
    changes = [(kind, value, old[(kind, value)], new[(kind, value)])
               for kind, value in sorted(old.keys() | new.keys())
               if old[(kind, value)] != new[(kind, value)]]
    issues: list[dict[str, Any]] = []
    if changes:
        old_lines, new_lines = line_starts(source), line_starts(draft)
        for kind, value, a, b in changes:
            key = (kind, value)
            source_offset, draft_offset = old_offsets.get(key), new_offsets.get(key)
            issues.append({"kind": "protected_content", "token_type": kind, "value": value,
                           "source_count": a, "draft_count": b,
                           "source_first_line": (bisect_right(old_lines, source_offset)
                                                 if source_offset is not None else None),
                           "draft_first_line": (bisect_right(new_lines, draft_offset)
                                                if draft_offset is not None else None)})
    if newline_types(source) != newline_types(draft):
        issues.append({"kind": "line_endings", "source": newline_types(source),
                       "draft": newline_types(draft)})
    if source.startswith("\ufeff") != draft.startswith("\ufeff"):
        issues.append({"kind": "byte_order_mark", "message": "UTF-8 BOM changed"})
    if ranges is not None:
        issues.extend(scope_findings(source, draft, ranges))
    return {"status": "review_required" if issues else "no_mechanical_issue",
            "issue_count": len(issues), "scope_checked": ranges is not None,
            "allowed_original_lines": ranges, "issues": issues,
            "limitations": "Heuristic text recognition and line diff only; not semantic or factual verification."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Recognizers are conservative, not a complete parser. Some overlapping tokens may "
        "produce related findings. Files are limited to 8 MiB each. No file is modified."))
    parser.add_argument("source", type=Path, help="Original UTF-8 file")
    parser.add_argument("draft", type=Path, help="Edited UTF-8 file")
    parser.add_argument("--allow-lines", action="append", default=None, metavar="START:END",
                        help="Permitted inclusive ORIGINAL line range; repeat for multiple sections")
    parser.add_argument("--protect", action="append", default=[], metavar="LITERAL",
                        help="Additional exact nonempty source text whose occurrence count must remain")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object")
    parser.add_argument("--diff", action="store_true", help="Include a unified diff in the report")
    args = parser.parse_args(argv)
    try:
        source, draft = read_utf8(args.source), read_utf8(args.draft)
        ranges = (parse_ranges(args.allow_lines, len(source.splitlines()))
                  if args.allow_lines is not None else None)
        result = compare(source, draft, literals=args.protect, ranges=ranges)
        result["source"] = str(args.source)
        result["draft"] = str(args.draft)
        if args.diff:
            result["diff"] = "".join(difflib.unified_diff(
                source.splitlines(keepends=True), draft.splitlines(keepends=True),
                fromfile=str(args.source), tofile=str(args.draft)))
    except (OSError, ValueError) as exc:
        error = {"status": "error", "message": str(exc)}
        print(json.dumps(error, ensure_ascii=False) if args.json else f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["status"] + f": {result['issue_count']} issue(s)")
        for issue in result["issues"]:
            print(json.dumps(issue, ensure_ascii=False))
        if args.diff:
            print(result["diff"], end="" if result["diff"].endswith("\n") else "\n")
        print(result["limitations"])
    return 1 if result["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
