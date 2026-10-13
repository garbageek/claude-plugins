"""Validate this repository's single Claude/Codex plugin and its local wiring."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    require(path.is_file(), f"{path}: missing JSON file")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    require(match is not None, f"{path}: missing YAML frontmatter")
    value = yaml.safe_load(match[1])
    require(isinstance(value, dict) and value, f"{path}: empty frontmatter")
    return value


def local_path(path, *, base=ROOT):
    require(isinstance(path, str) and path, f"Invalid local path: {path!r}")
    target = (base / path).resolve()
    require(target.is_relative_to(ROOT), f"Package path escapes the root: {path}")
    require(target.exists(), f"Missing package path: {path}")
    return target


def validate_manifests():
    claude = read_json(ROOT / ".claude-plugin/plugin.json")
    codex = read_json(ROOT / ".codex-plugin/plugin.json")
    require(not (ROOT / "plugin.json").exists(),
            "This toolkit uses the native Codex manifest for its shared skills and MCP configuration")
    require(not (ROOT / "plugins").exists(), "Remove obsolete nested plugin products")
    for key in ("name", "version", "description"):
        require(isinstance(claude.get(key), str) and claude[key], f"Missing Claude {key}")
        require(codex.get(key) == claude[key], f"Claude/Codex {key} mismatch")
    name = claude["name"]
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name), "Plugin name must be kebab-case")
    require(local_path(codex.get("skills")) == ROOT / "skills", "Codex must load the common skills")
    require("hooks" not in codex, "The Codex manifest must not register bundled hooks")
    require("mcpServers" not in claude and "mcpServers" not in codex,
            "Do not auto-register MCP servers in plugin manifests")
    require("hooks" not in claude, "Do not auto-register Claude hooks")
    interface = codex.get("interface", {})
    require(interface.get("category") == "Developer Tools", "Missing/incorrect Codex category")
    # The public directory applies stricter listing limits than ZIP upload.
    for key, max_length, multiline in (
        ("displayName", 30, False),
        ("shortDescription", 30, False),
        ("longDescription", 4000, True),
        ("developerName", 80, False),
    ):
        value = interface.get(key)
        require(isinstance(value, str) and value.strip() and len(value) <= max_length,
                f"Invalid public listing {key} (max {max_length} characters)")
        require("\r" not in value and (multiline or "\n" not in value),
                f"Public listing {key} must be single-line or LF-only text")
    capabilities = interface.get("capabilities")
    require(isinstance(capabilities, list) and len(capabilities) <= 20,
            "Public listing capabilities must be a list of at most 20 labels")
    require(all(isinstance(c, str) and c.strip() and len(c) <= 120 and "\n" not in c
                and "\r" not in c for c in capabilities),
            "Invalid public listing capability label")
    prompts = interface.get("defaultPrompt", [])
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Use one to three Codex default prompts")
    require(all(isinstance(p, str) and 0 < len(p) <= 128 for p in prompts), "Invalid Codex default prompt")
    normalized_prompts = [" ".join(p.split()) for p in prompts]
    require(all(p and "\n" not in p and "\r" not in p for p in prompts),
            "Codex default prompts must be nonempty and single-line")
    require(len(set(normalized_prompts)) == len(prompts),
            "Codex default prompts must be unique after whitespace normalization")
    for key in ("logo", "composerIcon"):
        if key in interface:
            require(local_path(interface[key]).is_file(), f"Missing {key}")
    return name, claude, codex


def validate_marketplaces(name, codex):
    for relative in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        catalog = read_json(ROOT / relative)
        entries = catalog.get("plugins")
        require(catalog.get("name") == "artur-plugins", f"{relative}: marketplace identity changed")
        require(isinstance(entries, list) and len(entries) == 1, f"{relative}: expected exactly one plugin")
        entry = entries[0]
        require(entry.get("name") == name, f"{relative}: plugin name mismatch")
        source = entry.get("source")
        if relative.startswith(".agents/"):
            require(isinstance(source, dict) and source.get("source") == "local", "Expected local Codex source")
            source = source.get("path")
            require(entry.get("category") == codex["interface"]["category"], "Marketplace category mismatch")
            policy = entry.get("policy", {})
            require(policy.get("installation") in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}, "Invalid installation policy")
            require(policy.get("authentication") in {"ON_INSTALL", "ON_FIRST_USE"}, "Invalid authentication policy")
        require(source == "./" and local_path(source) == ROOT, f"{relative}: plugin must be the repository root")
        require("version" not in entry and "version" not in catalog.get("metadata", {}),
                f"{relative}: do not duplicate release versions in catalog metadata")
    print("Marketplaces: one shared root plugin in each catalog")


def validate_skills(name):
    directories = sorted(path for path in (ROOT / "skills").iterdir()
                         if path.is_dir() and not path.name.startswith("."))
    require(directories, "Missing skills")
    skills = []
    for directory in directories:
        path = directory / "SKILL.md"
        require(path.is_file(), f"{directory}: skill directory has no SKILL.md")
        skills.append(path)
    names = set()
    for path in skills:
        meta = frontmatter(path)
        skill_name = meta.get("name")
        require(skill_name == path.parent.name, f"{path}: directory/name mismatch")
        require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name), f"{path}: invalid skill name")
        require(skill_name not in names, f"Duplicate skill: {skill_name}")
        names.add(skill_name)
        desc = meta.get("description")
        require(isinstance(desc, str) and 0 < len(desc) <= 1024, f"{path}: invalid description")
        require(len(f"{name}:{skill_name}") <= 64, f"{path}: namespaced identity exceeds repository limit")
    # This toolkit's promised plugin lifecycle, not a platform requirement.
    required = {"create-plugin", "inspect-plugin", "update-plugin", "install-agent-plugins"}
    missing = required - names
    require(not missing, f"Missing plugin lifecycle skills: {', '.join(sorted(missing))}")
    for path in (ROOT / "agents").glob("*.md"):
        meta = frontmatter(path)
        for skill in meta.get("skills", []):
            require(skill in names, f"{path}: references an absent skill {skill}")
    require(not (ROOT / "commands").exists(), "Init/status/next are shared skills, not duplicate commands")
    for path in (ROOT / "skills").glob("*/agents/openai.yaml"):
        meta = yaml.safe_load(path.read_text(encoding="utf-8"))
        require(isinstance(meta, dict), f"{path}: expected interface metadata")
        require("products" not in meta.get("policy", {}), f"{path}: product filtering is not used in this toolkit")
        for key in ("icon_small", "icon_large"):
            value = meta.get("interface", {}).get(key)
            if value:
                require(local_path(value, base=path.parent.parent).is_file(), f"{path}: missing {key}")
    print(f"Skills: {len(names)} unique shared entry points; agent references valid")


def validate_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "__pycache__"} for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        if path.suffix in {".yaml", ".yml"}:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r'\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text):
            parsed = urlsplit(link)
            if parsed.scheme or link.startswith(("#", "/")) or not parsed.path:
                continue
            local_path(unquote(parsed.path), base=path.parent)
    print("Package JSON/YAML and local Markdown links: valid")


def validate_audit_mcp():
    require(not (ROOT / "hooks").exists(), "Bundled hooks must be removed")
    require(not (ROOT / ".mcp.json").exists(),
            "Root .mcp.json would automatically register a Claude MCP connector")
    require(not (ROOT / "mcp.json").exists(),
            "Root mcp.json would automatically register a portable MCP connector")
    codex = read_json(ROOT / "mcp/codex.json")
    servers = codex.get("mcpServers", {})
    require(set(servers) == {"audit-workflow"}, "Optional Codex adapter must keep audit-workflow")
    server = servers["audit-workflow"]
    require(server.get("command") == "python3", "Codex: expected Python launcher")
    require(server.get("cwd") == ".", "Codex: expected relative plugin cwd")
    require(server.get("args") == ["mcp/audit_mcp_server.py"],
            "Codex: expected plugin-relative MCP path")
    env = server.get("env", {})
    require(env.get("AUDIT_REQUIRE_EXPLICIT_ROOT") == "1" and "AUDIT_PROJECT_DIR" not in env,
            "Codex: explicit project root must be required")
    require("AUDIT_PLUGIN_ROOT" not in env,
            "Codex: do not use unexpanded PLUGIN_ROOT in native MCP env")
    for relative in ("scripts/audit.py", "scripts/scatter_scan.py", "mcp/audit_mcp_server.py"):
        local_path(relative)
    print("Audit: CLI on request; no bundled hooks or auto-registered MCP server")


def main():
    name, claude, codex = validate_manifests()
    validate_marketplaces(name, codex)
    validate_skills(name)
    validate_files()
    validate_audit_mcp()
    print(f"{name}: package valid")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        raise SystemExit(1)
