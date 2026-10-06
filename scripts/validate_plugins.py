"""Validate marketplace sources and portable plugin artifacts."""

import json
import re
import struct
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    require(match is not None, f"{path}: missing YAML frontmatter")
    data = yaml.safe_load(match[1])
    require(isinstance(data, dict) and data, f"{path}: empty frontmatter")
    return data


def validate_plugin(entry):
    source = entry["source"]
    require(source.startswith("./plugins/"), f"Unsupported marketplace source: {source}")
    plugin = (ROOT / source).resolve()
    require(plugin.is_relative_to(ROOT / "plugins"), f"Invalid source: {source}")
    claude = read_json(plugin / ".claude-plugin/plugin.json")
    for key in ("name", "version"):
        require(claude[key] == entry[key], f"{plugin}: marketplace {key} mismatch")
    for path in plugin.rglob("*.json"):
        read_json(path)
    for path in plugin.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    skills = sorted((plugin / "skills").glob("*/SKILL.md"))
    require(skills, f"{plugin}: missing skills")
    for path in skills:
        meta = frontmatter(path)
        require(meta.get("name") == path.parent.name, f"{path}: skill name mismatch")
        require(isinstance(meta.get("description"), str) and meta["description"].strip(), f"{path}: missing description")
        require(len(meta["description"]) <= 1024, f"{path}: description exceeds 1024 characters")
        require(len(f'{entry["name"]}:{meta["name"]}') <= 64, f"{path}: identity exceeds 64 characters")
    for folder in ("agents", "commands"):
        for path in (plugin / folder).glob("*.md"):
            frontmatter(path)
    for path in plugin.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", text):
            parsed = urlsplit(link)
            if parsed.scheme or link.startswith(("#", "/")) or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            require(target.is_relative_to(plugin) and target.exists(), f"{path}: broken package link {link}")
    canonical_path = plugin / "plugin.json"
    compatibility_path = plugin / ".codex-plugin/plugin.json"
    if canonical_path.exists():
        canonical = read_json(canonical_path)
        compatibility = read_json(compatibility_path)
        for key in ("name", "version", "description"):
            require(canonical[key] == compatibility[key] == claude[key], f"{plugin}: manifest {key} mismatch")
        interface = canonical["extensions"]["com.openai"]["interface"]
        require(interface == compatibility["interface"], f"{plugin}: OpenAI interface mismatch")
        require((plugin / compatibility["skills"]).resolve() == plugin / "skills", f"{plugin}: skills path mismatch")
        for field in ("logo", "composerIcon"):
            asset = (plugin / interface[field]).resolve()
            require(asset.is_relative_to(plugin) and asset.is_file(), f"{plugin}: missing {field}")
            data = asset.read_bytes()
            require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", f"{asset}: expected PNG")
            width, height = struct.unpack(">II", data[16:24])
            require(width == height and 48 <= width <= 4096 and len(data) <= 5 * 1024 * 1024, f"{asset}: invalid icon dimensions or size")
    elif compatibility_path.exists():
        raise ValueError(f"{plugin}: Codex compatibility manifest has no canonical portable manifest")
    print(f'{entry["name"]} {entry["version"]}: artifacts valid ({len(skills)} skills)')


def main():
    marketplace = read_json(ROOT / ".claude-plugin/marketplace.json")
    entries = marketplace["plugins"]
    require(len({entry["name"] for entry in entries}) == len(entries), "Duplicate marketplace plugin names")
    for entry in entries:
        validate_plugin(entry)


if __name__ == "__main__":
    main()
