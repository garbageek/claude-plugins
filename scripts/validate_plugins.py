"""Validate Claude/OpenAI marketplace sources and plugin artifacts."""

import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = (ROOT / "plugins").resolve()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    require(path.is_file(), f"{path}: missing JSON file")
    return json.loads(path.read_text(encoding="utf-8"))


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    require(match is not None, f"{path}: missing YAML frontmatter")
    data = yaml.safe_load(match[1])
    require(isinstance(data, dict) and data, f"{path}: empty frontmatter")
    return data


def resolve_local_source(source):
    require(isinstance(source, str) and source.startswith("./plugins/"), f"Unsupported marketplace source: {source!r}")
    plugin = (ROOT / source).resolve()
    require(plugin.is_relative_to(PLUGINS_ROOT), f"Invalid source outside plugins/: {source}")
    require(plugin.is_dir(), f"Plugin source does not exist: {source}")
    return plugin


def validate_plugin(plugin, *, expected_name=None, claude_entry=None):
    claude_path = plugin / ".claude-plugin/plugin.json"
    claude = read_json(claude_path)
    if expected_name is not None:
        require(claude.get("name") == expected_name, f"{plugin}: marketplace name mismatch")
    if claude_entry and "version" in claude_entry:
        require(claude.get("version") == claude_entry["version"], f"{plugin}: marketplace version mismatch")

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
        require(len(f'{claude["name"]}:{meta["name"]}') <= 64, f"{path}: identity exceeds 64 characters")

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
        require(canonical.get("name") == claude.get("name"), f"{plugin}: portable/Claude name mismatch")
        require(canonical.get("version") == claude.get("version"), f"{plugin}: portable/Claude version mismatch")
        require(canonical.get("description") == claude.get("description"), f"{plugin}: portable/Claude description mismatch")
        if compatibility_path.exists():
            compatibility = read_json(compatibility_path)
            for key in ("name", "version", "description"):
                require(canonical[key] == compatibility[key], f"{plugin}: compatibility {key} mismatch")
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

    return claude, len(skills)


def validate_claude_marketplace():
    path = ROOT / ".claude-plugin/marketplace.json"
    marketplace = read_json(path)
    entries = marketplace.get("plugins")
    require(isinstance(entries, list) and entries, f"{path}: plugins must be a non-empty list")
    require(len({entry.get("name") for entry in entries}) == len(entries), f"{path}: duplicate plugin names")
    validated = {}
    for entry in entries:
        plugin = resolve_local_source(entry.get("source"))
        claude, skill_count = validate_plugin(plugin, expected_name=entry.get("name"), claude_entry=entry)
        validated[entry["name"]] = plugin
        print(f'Claude: {claude["name"]} {claude["version"]}: artifacts valid ({skill_count} skills)')
    return validated


def validate_openai_marketplace(claude_plugins):
    path = ROOT / ".agents/plugins/marketplace.json"
    marketplace = read_json(path)
    entries = marketplace.get("plugins")
    require(isinstance(entries, list) and entries, f"{path}: plugins must be a non-empty list")
    require(len({entry.get("name") for entry in entries}) == len(entries), f"{path}: duplicate plugin names")
    for entry in entries:
        name = entry.get("name")
        source = entry.get("source")
        require(isinstance(source, dict) and source.get("source") == "local", f"{path}: {name}: expected local source object")
        source_path = source.get("path")
        require(isinstance(source_path, str) and source_path.startswith("./"), f"{path}: {name}: source.path must start with ./")
        plugin = (ROOT / source_path).resolve()
        require(plugin.is_relative_to(ROOT) and plugin.is_relative_to(PLUGINS_ROOT), f"{path}: {name}: source.path escapes plugins root")
        require(plugin.is_dir(), f"{path}: {name}: plugin path does not exist")
        if name in claude_plugins:
            require(plugin == claude_plugins[name], f"{path}: {name}: source differs from Claude marketplace")
        canonical = read_json(plugin / "plugin.json")
        require(canonical.get("name") == name, f"{path}: {name}: canonical plugin.json name mismatch")
        policy = entry.get("policy")
        require(isinstance(policy, dict), f"{path}: {name}: missing policy")
        require(policy.get("installation") in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}, f"{path}: {name}: invalid installation policy")
        require(policy.get("authentication") in {"ON_INSTALL", "ON_FIRST_USE"}, f"{path}: {name}: invalid authentication policy")
        require(isinstance(entry.get("category"), str) and entry["category"].strip(), f"{path}: {name}: missing category")
        interface = canonical.get("extensions", {}).get("com.openai", {}).get("interface", {})
        require(entry["category"] == interface.get("category"), f"{path}: {name}: category differs from OpenAI plugin interface")
        validate_plugin(plugin, expected_name=name)
        print(f'OpenAI/Codex: {name} {canonical.get("version", "")}: marketplace entry valid')


def main():
    claude_plugins = validate_claude_marketplace()
    validate_openai_marketplace(claude_plugins)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        raise SystemExit(1)
