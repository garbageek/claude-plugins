from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import re

LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def transform_links(markdown: str, replace, pattern=LINK_RE) -> str:
    """Rewrite inline prose links without changing fenced/inline code examples."""
    output = []
    fence = ""
    for line in markdown.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if not fence:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = ""
            output.append(line)
        elif fence or line.startswith("    ") or line.startswith("\t"):
            output.append(line)
        else:
            offset = 0
            parts = []
            for code in re.finditer(r"(`+).*?\1", line):
                parts.extend([pattern.sub(replace, line[offset:code.start()]), code.group(0)])
                offset = code.end()
            parts.append(pattern.sub(replace, line[offset:]))
            output.append("".join(parts))
    return "".join(output)


def iter_markdown_links(markdown: str) -> list[tuple[int, str]]:
    lines = []
    fence = ""
    for line in markdown.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if not fence:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = ""
            lines.append("")
        else:
            lines.append("" if fence else re.sub(r"`+[^`]*`+", "", line))
    return [
        (number, match.group(1).strip())
        for number, line in enumerate(lines, 1)
        for match in LINK_RE.finditer(line)
    ]


def is_external_link(link: str) -> bool:
    parsed = urlparse(link)
    return bool(parsed.scheme or parsed.netloc) or link.startswith("#")


def split_link(link: str) -> tuple[str, str]:
    path = link.split("#", 1)[0].split("?", 1)[0]
    return unquote(path), link[len(path) :]


def resolve_markdown_link(source_file: Path, link: str) -> Path | None:
    if is_external_link(link):
        return None
    raw_path, _ = split_link(link)
    if not raw_path:
        return None
    return (source_file.parent / raw_path).resolve()


def markdown_link_failure_reason(source_file: Path, root: Path, link: str) -> str | None:
    target = resolve_markdown_link(source_file, link)
    if target is None:
        return None
    try:
        target.relative_to(root)
    except ValueError:
        return "link target is outside the wiki directory"
    if not target.exists():
        if target.suffix == ".md" and (target.with_suffix("") / "index.md").exists():
            suggestion = (target.with_suffix("") / "index.md").relative_to(root).as_posix()
            return f"file does not exist — did you mean {suggestion}?"
        return "file does not exist"
    return None


def markdown_link_target_exists(source_file: Path, root: Path, link: str) -> bool:
    return markdown_link_failure_reason(source_file, root, link) is None


def markdown_path_to_html(link: str) -> str:
    if is_external_link(link):
        return link
    raw_path, suffix = split_link(link)
    if not raw_path:
        return link
    if raw_path.endswith(".md"):
        raw_path = raw_path[:-3] + ".html"
    if raw_path.endswith("/index.html"):
        raw_path = raw_path[: -len("index.html")]
    return quote(raw_path, safe="/@:+") + suffix


def rewrite_markdown_links(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        link = match.group(1).strip()
        rewritten = markdown_path_to_html(link)
        return original[: original.rfind("(") + 1] + rewritten + ")"

    return LINK_RE.sub(replace, markdown)
