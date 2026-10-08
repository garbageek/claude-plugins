from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any

META_FILE = ".wiki-meta.json"
INDEX_START = "<!-- droid-wiki:index:start -->"
INDEX_END = "<!-- droid-wiki:index:end -->"

def semantic_sort_key(path: str) -> tuple:
    if path == "index.md":
        return (-1, "", 0, path)
    rel = Path(path)
    section = rel.parts[0] if len(rel.parts) > 1 else rel.stem
    is_index = 0 if rel.name == "index.md" else 1
    return (0, section, is_index, path)


@dataclass(frozen=True)
class Page:
    path: str
    id: str
    title: str
    summary: str
    section: str
    source_path: Path


def normalize_wiki_root(wiki_dir: str | Path) -> Path:
    root = Path(wiki_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Wiki directory does not exist or is not a directory: {root}")
    return root


def to_posix(path: Path) -> str:
    return path.as_posix()


def load_meta(wiki_dir: str | Path) -> dict[str, Any]:
    meta_path = normalize_wiki_root(wiki_dir) / META_FILE
    if not meta_path.exists():
        return {}
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise ValueError(f"{META_FILE} must contain a JSON object")
    return meta


def write_meta(wiki_dir: str | Path, meta: dict[str, Any]) -> None:
    meta_path = normalize_wiki_root(wiki_dir) / META_FILE
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def discover_markdown_files(wiki_dir: str | Path) -> list[str]:
    root = normalize_wiki_root(wiki_dir)
    paths = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Wiki pages must be ordinary files within the wiki: {path}")
        paths.append(to_posix(path.relative_to(root)))
    return sorted(paths)


def order_markdown_files(wiki_dir: str | Path, paths: list[str] | None = None) -> list[str]:
    paths = paths or discover_markdown_files(wiki_dir)
    meta = load_meta(wiki_dir)
    page_order = [path for path in meta.get("pageOrder", []) if isinstance(path, str)]
    seen: set[str] = set()
    ordered: list[str] = []
    path_set = set(paths)
    for path in page_order:
        if path in path_set and path not in seen:
            ordered.append(path)
            seen.add(path)
    remaining = sorted((path for path in paths if path not in seen), key=semantic_sort_key)
    ordered.extend(remaining)
    return ordered


def page_id_for_path(path: str) -> str:
    rel = Path(path)
    if rel.name == "index.md":
        if rel.parent == Path("."):
            return "index"
        return "--".join((*rel.parent.parts, "index"))
    without_suffix = rel.with_suffix("")
    return "--".join(without_suffix.parts)


def title_from_slug(slug: str) -> str:
    if not slug or slug == ".":
        return "Wiki"
    return slug.replace("-", " ").replace("_", " ").title()


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return title or fallback
    return fallback


def markdown_to_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_>#|]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_summary(markdown: str) -> str:
    in_fence = False
    lines: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line:
            if lines:
                break
            continue
        if line.startswith("#"):
            continue
        if line.lower().startswith("active contributors:"):
            continue
        if line.startswith("<!--"):
            continue
        if line.startswith("|") or line.startswith("- ") or line.startswith("* "):
            continue
        lines.append(line)
    summary = markdown_to_text(" ".join(lines))
    return summary[:240]


def collect_pages(wiki_dir: str | Path) -> list[Page]:
    root = normalize_wiki_root(wiki_dir)
    pages: list[Page] = []
    for rel_path in order_markdown_files(root):
        path = root / rel_path
        fallback = title_from_slug(Path(rel_path).stem if Path(rel_path).name != "index.md" else Path(rel_path).parent.name)
        markdown = path.read_text(encoding="utf-8")
        section = Path(rel_path).parts[0] if len(Path(rel_path).parts) > 1 else Path(rel_path).stem
        pages.append(
            Page(
                path=rel_path,
                id=page_id_for_path(rel_path),
                title=extract_title(markdown, fallback),
                summary=extract_summary(markdown),
                section=section,
                source_path=path,
            )
        )
    return pages


def page_order_from_pages(pages: list[Page]) -> list[str]:
    return [page.path for page in pages]


def top_level_sections_from_pages(pages: list[Page]) -> list[str]:
    sections: list[str] = []
    for page in pages:
        section = page.path.split("/", 1)[0]
        section = section[:-3] if section.endswith(".md") else section
        if section == "index":
            continue
        if section not in sections:
            sections.append(section)
    return sections


def anchor_slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
