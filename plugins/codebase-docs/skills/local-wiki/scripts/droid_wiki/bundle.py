from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict
from urllib.parse import quote, unquote
import re
import os

from .links import (
    LINK_RE,
    is_external_link,
    iter_markdown_links,
    markdown_link_failure_reason,
    resolve_markdown_link,
    split_link,
    transform_links,
)
from .model import Page, anchor_slug, collect_pages, normalize_wiki_root

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class BundleStats(TypedDict):
    pages: int
    bytes: int
    warnings: list[str]


def page_by_source_path(pages: list[Page]) -> dict[Path, Page]:
    return {page.source_path.resolve(): page for page in pages}


def rewrite_bundle_links(markdown: str, source_page: Page, pages_by_source: dict[Path, Page], root: Path, output_dir: Path | None = None) -> str:
    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        link = match.group(1).strip()
        if is_external_link(link):
            if link.startswith("#"):
                target = f"#{source_page.id}--{unquote(link[1:])}"
                return original[: original.rfind("(") + 1] + target + ")"
            return original

        raw_path, suffix = split_link(link)
        target_path = resolve_markdown_link(source_page.source_path, link)
        if target_path is None:
            return original
        if target_path.is_dir():
            target_path = target_path / "index.md"
        if target_path.suffix != ".md" and (target_path.with_suffix("") / "index.md").exists():
            target_path = target_path.with_suffix("") / "index.md"
        try:
            target_path.relative_to(root)
        except ValueError:
            return original

        target_page = pages_by_source.get(target_path.resolve())
        if target_page is None:
            if output_dir is not None and target_path.is_file() and target_path.suffix != ".md":
                relative = Path(os.path.relpath(target_path, output_dir)).as_posix()
                start, end = match.start(1) - match.start(), match.end(1) - match.start()
                return original[:start] + quote(relative, safe="/") + suffix + original[end:]
            return original

        target = f"#{target_page.id}"
        if suffix.startswith("#"):
            target = f"#{target_page.id}--{unquote(suffix[1:])}"
        elif raw_path == "":
            target = f"#{source_page.id}"
        return original[: original.rfind("(") + 1] + target + ")"

    return transform_links(markdown, replace, re.compile(r"!?\[[^\]]+\]\(([^)]+)\)"))


def add_heading_anchors(markdown: str, page: Page) -> str:
    lines: list[str] = []
    fence = ""
    seen: dict[str, int] = {}
    for line in markdown.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if not fence:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = ""
            lines.append(line)
            continue
        match = HEADING_RE.match(line) if not fence else None
        if match:
            slug = anchor_slug(match.group(2))
            if slug:
                count = seen.get(slug, 0)
                seen[slug] = count + 1
                suffix = f"-{count}" if count else ""
                lines.append(f'<a id="{page.id}--{slug}{suffix}"></a>')
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def render_markdown_bundle(wiki_dir: str | Path, title: str = "Local Wiki", output_dir: Path | None = None) -> str:
    root = normalize_wiki_root(wiki_dir)
    pages = collect_pages(root)
    if not pages:
        raise ValueError("No Markdown pages found")
    pages_by_source = page_by_source_path(pages)
    lines = [f"# {title}", "", "Generated from source-backed wiki pages; source page paths are recorded below.", "", "## Contents", ""]
    lines.extend(f"- [{page.title}](#{page.id}) — `{page.path}`" for page in pages)
    lines.append("")
    for page in pages:
        markdown = page.source_path.read_text(encoding="utf-8")
        markdown = rewrite_bundle_links(markdown, page, pages_by_source, root, output_dir)
        markdown = add_heading_anchors(markdown, page)
        lines.extend(["---", "", f'<a id="{page.id}"></a>', f"<!-- droid-wiki:source {page.path} -->", "", markdown.rstrip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def unresolved_local_link_warnings(wiki_dir: str | Path) -> list[str]:
    root = normalize_wiki_root(wiki_dir)
    warnings: list[str] = []
    seen: set[str] = set()
    for page in collect_pages(root):
        markdown = page.source_path.read_text(encoding="utf-8")
        for lineno, link in iter_markdown_links(markdown):
            reason = markdown_link_failure_reason(page.source_path, root, link)
            if reason:
                warning = f"unresolved local link: {page.path}:{lineno}: {link} ({reason})"
                if warning not in seen:
                    seen.add(warning)
                    warnings.append(warning)
    return warnings


def write_markdown_bundle(
    wiki_dir: str | Path, out: str | Path, title: str = "Local Wiki"
) -> BundleStats:
    root = normalize_wiki_root(wiki_dir)
    output = Path(out).expanduser()
    if output.is_symlink():
        raise ValueError(f"Refusing symlink output: {output}")
    output = output.resolve()
    if output.is_relative_to(root):
        raise ValueError("Bundle must live outside the source wiki")
    if output.exists():
        raise ValueError(f"Bundle destination already exists; choose a new file: {output}")
    markdown = render_markdown_bundle(root, title=title, output_dir=output.parent)
    warnings = unresolved_local_link_warnings(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(markdown)
    return {"pages": len(collect_pages(root)), "bytes": output.stat().st_size, "warnings": warnings}
