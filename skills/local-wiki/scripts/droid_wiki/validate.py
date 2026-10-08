from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path

from .links import iter_markdown_links, markdown_link_failure_reason, split_link, transform_links
from .model import (
    META_FILE,
    discover_markdown_files,
    load_meta,
    normalize_wiki_root,
    page_id_for_path,
    title_from_slug,
)

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
LINK_FULL_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for value in values:
        if value in seen:
            dupes.add(value)
        else:
            seen.add(value)
    return sorted(dupes)


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_wiki(wiki_dir: str | Path, max_page_bytes: int = 500 * 1024) -> ValidationResult:
    root = normalize_wiki_root(wiki_dir)
    errors: list[str] = []
    warnings: list[str] = []
    meta: dict = {}

    if not root.exists():
        return ValidationResult([f"Wiki directory does not exist: {root}"], warnings)

    meta_path = root / META_FILE
    if not meta_path.exists():
        errors.append(f"Missing {META_FILE}")
    else:
        try:
            meta = load_meta(root)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid {META_FILE}: {exc}")

    md_paths = discover_markdown_files(root)
    md_set = set(md_paths)

    from .finalize import wiki_directories
    for directory in wiki_directories(root):
        if not (directory / "index.md").exists():
            errors.append(f"Missing index.md in {directory.relative_to(root).as_posix()}")
    if not (root / "index.md").exists():
        errors.append("Missing root index.md")

    for rel in md_paths:
        path = root / rel
        if path.stat().st_size > max_page_bytes:
            errors.append(f"Page exceeds {max_page_bytes} bytes: {rel}")
        if not KEBAB_RE.match(path.name):
            warnings.append(f"Generated-page naming convention is lowercase kebab-case: {rel}")
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            errors.append(f"Markdown file must start with '# ': {rel}")
        for lineno, link in iter_markdown_links(text):
            reason = markdown_link_failure_reason(path, root, link)
            if reason:
                hint = " \u2014 use backticks instead of a markdown link" if "outside the wiki" in reason else ""
                error = f"Broken local link in {rel}:{lineno}: {link} ({reason}{hint})"
                if error not in errors:
                    errors.append(error)

    page_order = meta.get("pageOrder", []) if isinstance(meta, dict) else []
    if page_order:
        ordered = [path for path in page_order if isinstance(path, str)]
        duplicate_order_paths = duplicates(ordered)
        for rel in duplicate_order_paths:
            errors.append(f"Duplicate pageOrder path in .wiki-meta.json: {rel}")
        missing_from_order = sorted(md_set - set(ordered))
        missing_files = sorted(set(ordered) - md_set)
        for rel in missing_from_order:
            errors.append(f"Markdown file missing from pageOrder: {rel}")
        for rel in missing_files:
            errors.append(f"pageOrder references missing file: {rel}")
    elif meta_path.exists():
        errors.append("Missing or empty pageOrder in .wiki-meta.json")

    if isinstance(meta, dict) and meta_path.exists():
        page_count = meta.get("pageCount")
        if page_count != len(md_paths):
            errors.append(
                f"pageCount mismatch in .wiki-meta.json: expected {len(md_paths)}, got {page_count}"
            )

        raw_pages = meta.get("pages", [])
        if not isinstance(raw_pages, list) or not raw_pages:
            errors.append("Missing or empty pages in .wiki-meta.json")
        else:
            page_paths: list[str] = []
            page_ids: list[str] = []
            for index, page in enumerate(raw_pages):
                if not isinstance(page, dict):
                    errors.append(f"Invalid page entry in .wiki-meta.json at index {index}")
                    continue
                rel = page.get("path")
                page_id = page.get("id")
                if not isinstance(rel, str):
                    errors.append(f"Invalid page path in .wiki-meta.json at index {index}")
                    continue
                page_paths.append(rel)
                if not isinstance(page_id, str) or not page_id:
                    errors.append(f"Missing page id in .wiki-meta.json for {rel}")
                    continue
                page_ids.append(page_id)
                expected_id = page_id_for_path(rel)
                if page_id != expected_id:
                    errors.append(
                        f"page id mismatch in .wiki-meta.json for {rel}: expected {expected_id}, got {page_id}"
                    )

            for page_id in duplicates(page_ids):
                errors.append(f"Duplicate page id in .wiki-meta.json: {page_id}")
            for rel in duplicates(page_paths):
                errors.append(f"Duplicate page path in .wiki-meta.json: {rel}")

            page_path_set = set(page_paths)
            for rel in sorted(md_set - page_path_set):
                errors.append(f"Markdown file missing from pages: {rel}")
            for rel in sorted(page_path_set - md_set):
                errors.append(f"pages references missing file: {rel}")

            if page_order:
                ordered_set = {path for path in page_order if isinstance(path, str)}
                for rel in sorted(ordered_set - page_path_set):
                    errors.append(f"pageOrder path missing from pages: {rel}")
                for rel in sorted(page_path_set - ordered_set):
                    errors.append(f"pages path missing from pageOrder: {rel}")

    return ValidationResult(errors, warnings)


def fallback_title(rel: str) -> str:
    path = Path(rel)
    stem = path.parent.name if path.name == "index.md" else path.stem
    return title_from_slug(stem)


def fix_links_in_text(source_file: Path, root: Path, text: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    def replace(match: re.Match[str]) -> str:
        anchor, link = match.group(1), match.group(2).strip()
        reason = markdown_link_failure_reason(source_file, root, link)
        if reason and reason.startswith("link target is outside"):
            changes.append(f"external link -> backticks: {link}")
            return f"`{anchor}`"
        if reason and reason.startswith("file does not exist — did you mean"):
            raw_path, suffix = split_link(link)
            new_path = raw_path[:-3] + "/index.md"
            changes.append(f"{raw_path} -> {new_path}")
            return f"[{anchor}]({new_path}{suffix})"
        return match.group(0)

    return transform_links(text, replace, LINK_FULL_RE), changes


def fix_wiki(wiki_dir: str | Path) -> list[tuple[str, str]]:
    root = normalize_wiki_root(wiki_dir)
    applied: list[tuple[str, str]] = []
    for rel in discover_markdown_files(root):
        path = root / rel
        text = path.read_text(encoding="utf-8")
        original = text
        if not text.startswith("# "):
            text = f"# {fallback_title(rel)}\n\n{text}"
            applied.append((rel, "prepended missing '# ' heading"))
        text, link_changes = fix_links_in_text(path, root, text)
        applied.extend((rel, change) for change in link_changes)
        if text != original:
            path.write_text(text, encoding="utf-8")
    return applied
