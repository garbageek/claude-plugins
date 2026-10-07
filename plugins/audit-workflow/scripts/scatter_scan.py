#!/usr/bin/env python3
"""
scatter_scan.py — locality-of-change signal scanner.

Surfaces *candidates* for Feature Scattering / Shotgun Surgery / Divergent Change.
It does NOT classify or write tickets — it produces evidence the auditor reads,
verifies, and may explicitly ticketize through the public audit contract.

Two independent signals:

  1. TERM SPREAD (static)   — for each feature term / flag, how many files and how
                              many distinct top-level modules contain it. A term that
                              appears in many files across many modules with no single
                              owning module is a Feature Scattering candidate.

  2. CO-CHANGE (git)        — files that repeatedly change together in the same commit.
                              High co-change across unrelated modules is a Shotgun
                              Surgery candidate. A single file co-changing with many
                              unrelated files for unrelated reasons is a Divergent
                              Change candidate.

Pure stdlib. Git signal is optional; unavailable, failed, disabled, and available are distinct.
No files or tickets are written. Coverage and scope are included in both outputs.

Usage:
    python scatter_scan.py PATH [options]

    # auto-discover candidate terms (feature flags, FEATURE_*, enable_*, *_enabled)
    python scatter_scan.py ./repo

    # explicit terms (feature names, flag names, business-rule identifiers)
    python scatter_scan.py ./repo --terms dark_mode promo_v2 LEGACY_CHECKOUT

    # tune thresholds and emit machine-readable output
    python scatter_scan.py ./repo --min-files 3 --min-modules 2 --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from itertools import combinations
from pathlib import Path

# ----------------------------------------------------------------------------- config

DEFAULT_IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    "env", "dist", "build", "target", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".idea", ".vscode", "vendor", ".next", ".cache",
    "coverage", "htmlcov", "site-packages", ".terraform",
}

CODE_EXTS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs",
    ".java", ".kt", ".kts", ".rb", ".php", ".cs", ".cpp", ".cc", ".cxx", ".c",
    ".h", ".hpp", ".scala", ".swift", ".m", ".mm", ".sql", ".sh", ".bash",
    ".toml", ".yaml", ".yml", ".json", ".tf", ".hcl",
}

# auto-discovery patterns for flag-like / feature-like identifiers
AUTO_TERM_PATTERNS = [
    re.compile(r"\bFEATURE_[A-Z0-9_]{2,}\b"),
    re.compile(r"\bFLAG_[A-Z0-9_]{2,}\b"),
    re.compile(r"\benable_([a-z0-9_]{2,})\b"),
    re.compile(r"\b([a-z0-9_]{2,})_enabled\b"),
    re.compile(r"\bis_([a-z0-9_]{2,})_(?:on|enabled|active)\b"),
    re.compile(r"\buse_([a-z0-9_]{2,})\b"),
]

MAX_FILE_BYTES = 2_000_000  # skip files larger than this


# ----------------------------------------------------------------------------- model

@dataclass
class TermSpread:
    term: str
    files: list[str] = field(default_factory=list)
    modules: set[str] = field(default_factory=set)
    hits: int = 0

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def module_count(self) -> int:
        return len(self.modules)

    def strength(self) -> str:
        f, m = self.file_count, self.module_count
        if f >= 8 and m >= 4:
            return "high"
        if f >= 5 and m >= 3:
            return "medium"
        return "low"


@dataclass
class CoChangePair:
    a: str
    b: str
    count: int
    cross_module: bool


# ----------------------------------------------------------------------------- helpers

def top_module(rel_path: str) -> str:
    """Directory-based locality proxy, not an inferred architectural owner."""
    parts = Path(rel_path).parts[:-1]
    if parts and parts[0] in {"src", "app", "lib", "pkg", "internal", "cmd"}:
        parts = parts[1:]
    return parts[0] if parts else "."


def in_scope(rel: str, scopes: list[str]) -> bool:
    path = Path(rel)
    return any(scope == "." or path == Path(scope) or Path(scope) in path.parents for scope in scopes)


def excluded_path(rel: str, ignore: set[str]) -> bool:
    parts = Path(rel).parts
    return any(part.startswith(".") for part in parts) or any(part in ignore for part in parts[:-1])


def read_sources(root: Path, scopes: list[str], ignore: set[str]) -> tuple[list[tuple[Path, str]], dict]:
    coverage = {
        "scope": scopes,
        "included_extensions": sorted(CODE_EXTS),
        "extensionless_included": True,
        "hidden_paths_included": False,
        "excluded_directory_names": sorted(ignore),
        "excluded_paths": [], "excluded_extensions": {},
        "oversized_files": [], "unreadable_files": [], "binary_files": [],
        "symlinks_skipped": [], "max_file_bytes": MAX_FILE_BYTES,
        "files_scanned": 0,
    }
    files = []
    def walk_error(exc):
        coverage["unreadable_files"].append({"path": str(exc.filename), "error": str(exc)})
    for directory, dirs, names in os.walk(root, onerror=walk_error):
        kept = []
        for name in sorted(dirs):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            # Traverse ancestors of the selected scopes, but nothing unrelated.
            if not in_scope(rel, scopes) and not any(Path(rel) in Path(s).parents for s in scopes):
                continue
            if path.is_symlink():
                coverage["symlinks_skipped"].append(rel)
            elif excluded_path(rel + "/_", ignore):
                coverage["excluded_paths"].append(rel + "/")
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            if not in_scope(rel, scopes):
                continue
            if path.is_symlink():
                coverage["symlinks_skipped"].append(rel)
                continue
            if excluded_path(rel, ignore):
                coverage["excluded_paths"].append(rel)
                continue
            ext = path.suffix.lower()
            if ext and ext not in CODE_EXTS:
                coverage["excluded_extensions"][ext] = coverage["excluded_extensions"].get(ext, 0) + 1
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    coverage["oversized_files"].append(rel)
                    continue
                text = path.read_text(encoding="utf-8")
                if "\x00" in text:
                    coverage["binary_files"].append(rel)
                    continue
            except (OSError, UnicodeError) as exc:
                coverage["unreadable_files"].append({"path": rel, "error": str(exc)})
                continue
            files.append((path, text))
    coverage["files_scanned"] = len(files)
    return files, coverage


def discover_terms(files: list[tuple[Path, str]], top_n: int) -> list[str]:
    counter: Counter[str] = Counter()
    for _, text in files:
        for pat in AUTO_TERM_PATTERNS:
            for match in pat.finditer(text):
                token = match.group(1) if match.groups() else match.group(0)
                token = token.strip("_").lower()
                if len(token) >= 3 and token not in {"the", "and", "for", "use"}:
                    counter[token] += 1
    # only terms seen more than once are interesting
    return [t for t, c in counter.most_common(top_n) if c > 1]


def build_word_regex(term: str) -> re.Pattern:
    # Match the term as an identifier *segment*: it must start at an identifier
    # segment boundary on the left (including underscore), but may continue on the right so the same feature
    # concept is found across naming variants (dark_mode -> dark_mode_enabled,
    # promo_v2 -> promo_v2_apply). Case-insensitive, underscore-aware.
    esc = re.escape(term)
    return re.compile(rf"(?<![A-Za-z0-9]){esc}[A-Za-z0-9_]*", re.IGNORECASE)


def scan_terms(
    files: list[tuple[Path, str]], root: Path, terms: list[str]
) -> list[TermSpread]:
    regexes = {t: build_word_regex(t) for t in terms}
    spreads = {t: TermSpread(term=t) for t in terms}
    for fp, text in files:
        rel = fp.relative_to(root).as_posix()
        for term, rx in regexes.items():
            hits = len(rx.findall(text))
            if hits:
                sp = spreads[term]
                sp.files.append(rel)
                sp.modules.add(top_module(rel))
                sp.hits += hits
    return list(spreads.values())


def git_commits(root: Path, args, scopes: list[str], ignore: set[str]) -> tuple[list[list[str]], dict]:
    history = {"status": "disabled" if args.no_git else "unavailable", "reason": None,
               "commit_limit": args.git_commits, "commits_read": 0, "commits_in_scope": 0,
               "max_commit_files": args.co_max_commit, "oversized_commits": [],
               "filtered_paths": 0, "shallow": None}
    if args.no_git:
        history["reason"] = "Disabled by --no-git"
        return [], history

    def run(*command):
        return subprocess.run(["git", "-C", str(root), *command], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=60)
    try:
        top = run("rev-parse", "--show-toplevel")
        if top.returncode:
            history["reason"] = top.stderr.strip() or "No accessible Git working tree"
            history["returncode"] = top.returncode
            return [], history
        git_root = Path(top.stdout.strip()).resolve()
        shallow = run("rev-parse", "--is-shallow-repository")
        history["shallow"] = shallow.stdout.strip() == "true" if shallow.returncode == 0 else None
        head = run("rev-parse", "--verify", "HEAD")
        if head.returncode:
            # An empty repository is available but has no commits; broken HEAD is failed.
            symbolic = run("symbolic-ref", "-q", "HEAD")
            refs = run("show-ref")
            if symbolic.returncode == 0 and refs.returncode == 1 and not refs.stdout:
                history.update(status="available", reason="Repository has no commits")
            else:
                history.update(status="failed", reason=head.stderr.strip(), returncode=head.returncode)
            return [], history
        out = run("log", f"-n{args.git_commits}", "--no-merges", "--no-renames",
                  "--name-only", "-z", "--format=%x00commit:%H%x00")
        if out.returncode:
            history.update(status="failed", reason=out.stderr.strip() or "git log failed", returncode=out.returncode)
            return [], history
    except FileNotFoundError:
        history["reason"] = "Git executable unavailable"
        return [], history
    except (OSError, subprocess.TimeoutExpired) as exc:
        history.update(status="failed", reason=str(exc))
        return [], history

    commits = []
    commit_id = None
    changed = []
    def finish():
        if commit_id is None:
            return
        history["commits_read"] += 1
        if len(changed) > args.co_max_commit:
            history["oversized_commits"].append({"commit": commit_id, "files": len(changed)})
            return
        selected = []
        for filename in changed:
            try:
                rel = (git_root / filename).relative_to(root).as_posix()
            except ValueError:
                history["filtered_paths"] += 1
                continue
            ext = Path(rel).suffix.lower()
            if not in_scope(rel, scopes) or excluded_path(rel, ignore) or (ext and ext not in CODE_EXTS):
                history["filtered_paths"] += 1
                continue
            selected.append(rel)
        if selected:
            commits.append(selected)
            history["commits_in_scope"] += 1
    first_path = False
    for token in out.stdout.split("\x00"):
        if re.fullmatch(r"commit:[0-9a-f]{40,64}", token):
            finish()
            commit_id, changed, first_path = token[7:], [], True
        elif token:
            # Git inserts one newline between the format and the first name.
            if first_path and token.startswith("\n"):
                token = token[1:]
            first_path = False
            if token:
                changed.append(token)
    finish()
    history["status"] = "available"
    history["reason"] = "Only non-merge commits within the history limit are considered"
    return commits, history


def co_change(commits: list[list[str]], min_count: int, max_commit_size: int):
    pair_counts: Counter[tuple[str, str]] = Counter()
    file_partners: dict[str, set[str]] = defaultdict(set)
    for files in commits:
        files = sorted(set(files))
        if len(files) < 2 or len(files) > max_commit_size:
            continue  # giant commits (bulk reformat, vendoring) add noise
        for a, b in combinations(files, 2):
            pair_counts[(a, b)] += 1
            file_partners[a].add(b)
            file_partners[b].add(a)

    pairs = [
        CoChangePair(a=a, b=b, count=c, cross_module=top_module(a) != top_module(b))
        for (a, b), c in pair_counts.items()
        if c >= min_count
    ]
    pairs.sort(key=lambda p: (-p.count, not p.cross_module))

    # divergent-change signal: a file partnered with many distinct files across modules
    divergent = []
    for f, partners in file_partners.items():
        mods = {top_module(p) for p in partners}
        if len(partners) >= 6 and len(mods) >= 3:
            divergent.append((f, len(partners), len(mods)))
    divergent.sort(key=lambda x: (-x[1], -x[2]))
    return pairs, divergent


# ----------------------------------------------------------------------------- report

def render_markdown(root, spreads, pairs, divergent, args, coverage, history) -> str:
    L = []
    L.append("# Scatter Scan — Locality Signals\n")
    L.append(f"**Root:** `{root}`  ")
    L.append(f"**Term spread threshold:** files >= {args.min_files}, modules >= {args.min_modules}\n")

    flagged = sorted(
        (s for s in spreads if s.file_count >= args.min_files and s.module_count >= args.min_modules),
        key=lambda s: (-s.module_count, -s.file_count),
    )

    L.append("## Coverage\n")
    L.append("```json\n" + json.dumps({"source": coverage, "history": history}, indent=2) + "\n```\n")
    L.append("Top-level module names and signal strength are heuristics, not defect severity.\n")
    L.append("## Term Spread (Feature Scattering candidates)\n")
    if not flagged:
        L.append("_No terms crossed the threshold._\n")
    else:
        L.append("| term | files | modules | hits | signal |")
        L.append("|------|-------|---------|------|--------|")
        for s in flagged:
            mods = ", ".join(sorted(s.modules))
            L.append(f"| `{s.term}` | {s.file_count} | {s.module_count} | {s.hits} | {s.strength()} |")
        L.append("")
        for s in flagged:
            L.append(f"### `{s.term}` — {s.module_count} modules, {s.file_count} files")
            L.append(f"modules: {', '.join(sorted(s.modules))}")
            for f in sorted(s.files):
                L.append(f"  - {f}")
            L.append("")

    L.append("## Co-Change Pairs (Shotgun Surgery candidates)\n")
    if not pairs:
        L.append("_No pairs over threshold in the inspected history._\n" if history["status"] == "available" else f"_Co-change unavailable: history is {history['status']}._\n")
    else:
        L.append("| count | cross-module | file A | file B |")
        L.append("|-------|--------------|--------|--------|")
        for p in pairs[:40]:
            x = "yes" if p.cross_module else "no"
            L.append(f"| {p.count} | {x} | {p.a} | {p.b} |")
        L.append("")

    L.append("## High-Fanout Files (Divergent Change candidates)\n")
    if not divergent:
        L.append("_None over threshold in the inspected history._\n" if history["status"] == "available" else "_Not measured: history unavailable._\n")
    else:
        L.append("| file | distinct co-changed files | distinct modules |")
        L.append("|------|---------------------------|------------------|")
        for f, n, m in divergent[:30]:
            L.append(f"| {f} | {n} | {m} |")
        L.append("")

    if history["status"] == "available":
        L.append(f"Reported {min(len(pairs), 40)} of {len(pairs)} qualifying pairs and {min(len(divergent), 30)} of {len(divergent)} high-fanout files.\n")
    L.append("---")
    L.append("_Signals are candidates, not verdicts. Open each flagged file, confirm the")
    L.append("actual behavior and change cost. Ticketization requires an explicit request._")
    return "\n".join(L) + "\n"


def build_json(root, spreads, pairs, divergent, args, coverage, history) -> dict:
    return {
        "root": str(root),
        "coverage": coverage,
        "history": history,
        "co_change_measured": history["status"] == "available",
        "pairs_total": len(pairs) if history["status"] == "available" else None,
        "pairs_reported": min(len(pairs), 100) if history["status"] == "available" else None,
        "thresholds": {"min_files": args.min_files, "min_modules": args.min_modules},
        "term_spread": [
            {
                "term": s.term,
                "files": sorted(s.files),
                "modules": sorted(s.modules),
                "file_count": s.file_count,
                "module_count": s.module_count,
                "hits": s.hits,
                "signal": s.strength(),
                "flagged": s.file_count >= args.min_files and s.module_count >= args.min_modules,
            }
            for s in sorted(spreads, key=lambda s: (-s.module_count, -s.file_count))
        ],
        "co_change_pairs": [asdict(p) for p in pairs[:100]] if history["status"] == "available" else None,
        "divergent_files": [
            {"file": f, "partners": n, "modules": m} for f, n, m in divergent
        ] if history["status"] == "available" else None,
    }


# ----------------------------------------------------------------------------- main

def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Locality-of-change signal scanner.")
    ap.add_argument("path", help="repo or directory to scan")
    ap.add_argument("--scope", action="append", help="repository-relative file/directory; repeat for multiple scopes (default: .)")
    ap.add_argument("--terms", nargs="*", default=None,
                    help="explicit feature/flag terms; if omitted, auto-discover")
    ap.add_argument("--min-files", type=positive_int, default=3,
                    help="min files a term must appear in to flag (default 3)")
    ap.add_argument("--min-modules", type=positive_int, default=2,
                    help="min distinct top-level modules to flag (default 2)")
    ap.add_argument("--auto-top", type=positive_int, default=40,
                    help="max auto-discovered terms to test (default 40)")
    ap.add_argument("--no-git", action="store_true", help="skip git co-change signal")
    ap.add_argument("--git-commits", type=positive_int, default=1000,
                    help="how many recent commits to scan (default 1000)")
    ap.add_argument("--co-min", type=positive_int, default=3,
                    help="min co-change count to report a pair (default 3)")
    ap.add_argument("--co-max-commit", type=positive_int, default=30,
                    help="ignore commits touching more than N files (default 30)")
    ap.add_argument("--ignore", nargs="*", default=[],
                    help="extra directory names to ignore")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = ap.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    scopes = []
    for raw in args.scope or ["."]:
        path = root / raw
        if Path(raw).is_absolute() or not path.resolve().is_relative_to(root) or not path.exists():
            ap.error(f"scope must be an existing repository-relative path: {raw}")
        scopes.append(path.resolve().relative_to(root).as_posix())
    ignore = DEFAULT_IGNORE_DIRS | set(args.ignore)
    files, coverage = read_sources(root, scopes, ignore)
    terms = list(dict.fromkeys(t for t in args.terms if t.strip())) if args.terms is not None else discover_terms(files, args.auto_top)
    if args.terms is not None and not terms:
        ap.error("--terms requires at least one non-empty term")
    spreads = scan_terms(files, root, terms) if terms else []
    commits, history = git_commits(root, args, scopes, ignore)
    pairs, divergent = co_change(commits, args.co_min, args.co_max_commit)
    if not files:
        print("warning: no readable source files in the selected coverage", file=sys.stderr)
    if history["status"] in {"failed", "unavailable"}:
        print(f"warning: Git history {history['status']}: {history['reason']}", file=sys.stderr)

    if args.json:
        print(json.dumps(build_json(root, spreads, pairs, divergent, args, coverage, history), indent=2))
    else:
        print(render_markdown(root, spreads, pairs, divergent, args, coverage, history))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # downstream closed the pipe (e.g. `| head`); exit quietly
        try:
            sys.stdout.close()
        except Exception:
            pass
        raise SystemExit(0)
