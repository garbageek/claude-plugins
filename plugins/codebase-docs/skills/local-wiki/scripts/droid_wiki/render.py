from __future__ import annotations

from markdown_it import MarkdownIt

from .links import markdown_path_to_html
from .model import anchor_slug, markdown_to_text


def render_markdown(markdown: str) -> str:
    md = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")
    tokens = md.parse(markdown)
    seen: dict[str, int] = {}
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and index + 1 < len(tokens):
            slug = anchor_slug(tokens[index + 1].content)
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            token.attrSet("id", f"{slug}-{count}" if count else slug)
        for child in token.children or []:
            if child.type == "link_open":
                href = child.attrGet("href")
                if href:
                    child.attrSet("href", markdown_path_to_html(href))
    # Mermaid and other fenced languages remain readable code offline.
    return md.renderer.render(tokens, md.options, {})


def plain_text_from_markdown(markdown: str) -> str:
    return markdown_to_text(markdown)
