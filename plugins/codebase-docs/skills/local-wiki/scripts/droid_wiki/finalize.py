from __future__ import annotations

from datetime import datetime, timezone
import subprocess
import re
from pathlib import Path
from typing import Any

from .model import (
    INDEX_END,
    INDEX_START,
    META_FILE,
    collect_pages,
    discover_markdown_files,
    extract_summary,
    extract_title,
    load_meta,
    normalize_wiki_root,
    order_markdown_files,
    page_id_for_path,
    title_from_slug,
    top_level_sections_from_pages,
    write_meta,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_value(repo: Path | None, args: list[str]) -> str | None:
    if repo is None:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def git_metadata(repo: str | Path | None) -> dict[str, str | None]:
    repo_path = Path(repo).expanduser().resolve() if repo else None
    return {
        "repoRoot": "." if repo_path else None,
        "repoUrl": git_value(repo_path, ["remote", "get-url", "origin"]),
        "branch": git_value(repo_path, ["branch", "--show-current"]),
        "commitHash": git_value(repo_path, ["rev-parse", "HEAD"]),
    }


def heading_for_index(directory: Path, root: Path) -> str:
    if directory == root:
        return "Wiki"
    return title_from_slug(directory.name)


def index_intro(directory: Path, root: Path) -> str:
    if directory == root:
        return "Start with the project overview or choose a section below."
    return f"Pages in the {title_from_slug(directory.name)} section."


def relative_link(from_file: Path, to_file: Path) -> str:
    return Path(to_file).relative_to(from_file.parent).as_posix() if to_file.parent == from_file.parent else Path(
        __import__("os").path.relpath(to_file, start=from_file.parent)
    ).as_posix()


def directory_children(root: Path, directory: Path, ordered_paths: list[str]) -> list[tuple[str, str, str]]:
    child_paths: set[str] = set()
    for rel in discover_markdown_files(root):
        path = root / rel
        try:
            relative = path.relative_to(directory)
        except ValueError:
            continue
        if len(relative.parts) == 1 and relative.name != "index.md":
            child_paths.add(rel)
        elif len(relative.parts) == 2 and relative.parts[1] == "index.md":
            child_paths.add(rel)

    ordered = [rel for rel in ordered_paths if rel in child_paths]
    ordered.extend(sorted(child_paths - set(ordered)))
    rows: list[tuple[str, str, str]] = []
    index_file = directory / "index.md"
    for rel in ordered:
        page_file = root / rel
        markdown = page_file.read_text(encoding="utf-8")
        title = extract_title(markdown, title_from_slug(Path(rel).stem))
        summary = extract_summary(markdown)
        rows.append((relative_link(index_file, page_file), title, summary))
    return rows


def build_index_block(root: Path, directory: Path, ordered_paths: list[str]) -> str:
    rows = directory_children(root, directory, ordered_paths)
    lines = [INDEX_START]
    if rows:
        lines.extend(["| Page | Summary |", "|---|---|"])
        for link, title, summary in rows:
            safe_summary = summary.replace("|", "\\|")
            lines.append(f"| [{title}]({link}) | {safe_summary} |")
    else:
        lines.append("No child pages found.")
    lines.append(INDEX_END)
    return "\n".join(lines)


def replace_or_append_index_block(existing: str, block: str) -> str:
    pattern = re.compile(
        rf"{re.escape(INDEX_START)}.*?{re.escape(INDEX_END)}",
        flags=re.DOTALL,
    )
    if pattern.search(existing):
        return pattern.sub(lambda _: block, existing).rstrip() + "\n"
    return existing.rstrip() + "\n\n" + block + "\n"


def wiki_directories(root: Path) -> list[Path]:
    dirs = {root}
    for rel in discover_markdown_files(root):
        parent = (root / rel).parent
        while parent != root.parent and root in [parent, *parent.parents]:
            dirs.add(parent)
            if parent == root:
                break
            parent = parent.parent
    return sorted(dirs, key=lambda path: (len(path.relative_to(root).parts), path.as_posix()))


def ensure_index_files(root: Path) -> None:
    directories = wiki_directories(root)
    # Make every section index discoverable before building any parent navigation.
    for directory in directories:
        index_file = directory / "index.md"
        if not index_file.exists():
            with index_file.open("x", encoding="utf-8") as stream:
                stream.write(f"# {heading_for_index(directory, root)}\n\n{index_intro(directory, root)}\n")
    ordered_paths = order_markdown_files(root)
    for directory in reversed(directories):
        index_file = directory / "index.md"
        block = build_index_block(root, directory, ordered_paths)
        existing = index_file.read_text(encoding="utf-8")
        index_file.write_text(replace_or_append_index_block(existing, block), encoding="utf-8")


def normalized_meta(root: Path, repo: str | Path | None = None) -> dict[str, Any]:
    previous = load_meta(root)
    pages = collect_pages(root)
    git = git_metadata(repo)
    return {
        "schemaVersion": 1,
        "generatedAt": previous.get("generatedAt") or utc_now(),
        "finalizedAt": utc_now(),
        "repoRoot": git["repoRoot"],
        "repoUrl": git["repoUrl"],
        "branch": git["branch"],
        "commitHash": git["commitHash"],
        "pageCount": len(pages),
        "topLevelSections": top_level_sections_from_pages(pages),
        "pageOrder": [page.path for page in pages],
        "pages": [
            {
                "id": page.id,
                "path": page.path,
                "title": page.title,
                "summary": page.summary,
                "section": page.section,
            }
            for page in pages
        ],
        "skipped": previous.get("skipped", []),
    }


def finalize_wiki(wiki_dir: str | Path, repo: str | Path | None = None) -> dict[str, Any]:
    root = normalize_wiki_root(wiki_dir)
    if not root.exists():
        raise FileNotFoundError(f"Wiki directory does not exist: {root}")
    load_meta(root)  # Validate existing metadata before any source writes.
    collect_pages(root)  # Also preflight page paths and text.
    ensure_index_files(root)
    meta = normalized_meta(root, repo=repo)
    write_meta(root, meta)
    return meta
