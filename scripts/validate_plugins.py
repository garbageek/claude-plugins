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
            "This toolkit uses the native Codex loader for hooks; a portable root changes that loading path")
    require(not (ROOT / "plugins").exists(), "Remove obsolete nested plugin products")
    for key in ("name", "version", "description"):
        require(isinstance(claude.get(key), str) and claude[key], f"Missing Claude {key}")
        require(codex.get(key) == claude[key], f"Claude/Codex {key} mismatch")
    name = claude["name"]
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name), "Plugin name must be kebab-case")
    require(local_path(codex.get("skills")) == ROOT / "skills", "Codex must load the common skills")
    require(local_path(codex.get("hooks")) == ROOT / "hooks/codex.json", "Incorrect Codex hook adapter")
    require(local_path(codex.get("mcpServers")) == ROOT / "mcp/codex.json", "Incorrect Codex MCP adapter")
    interface = codex.get("interface", {})
    require(interface.get("category") == "Developer Tools", "Missing/incorrect Codex category")
    prompts = interface.get("defaultPrompt", [])
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3, "Use one to three Codex default prompts")
    require(all(isinstance(p, str) and 0 < len(p) <= 128 for p in prompts), "Invalid Codex default prompt")
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


def validate_audit_adapters():
    modes = {"SessionStart": "session-start", "PreToolUse": "pre-tool-use", "PostToolUse": "post-tool-use", "Stop": "stop"}
    for host, relative, variable in (("Claude", "hooks/hooks.json", "CLAUDE_PLUGIN_ROOT"),
                                     ("Codex", "hooks/codex.json", "PLUGIN_ROOT")):
        hooks = read_json(ROOT / relative)["hooks"]
        require(set(hooks) == set(modes), f"{host}: hook event coverage differs")
        for event, groups in hooks.items():
            require(isinstance(groups, list) and groups, f"{host}: missing {event} handler")
            if event in {"PreToolUse", "PostToolUse"}:
                matchers = [re.compile(group.get("matcher", ".*")) for group in groups]
                covered = ("Bash", "Edit", "Write", "MultiEdit") + (("apply_patch",) if host == "Codex" else ())
                require(all(any(m.search(tool) for m in matchers) for tool in covered), f"{host}: missing tool coverage")
            for group in groups:
                for handler in group["hooks"]:
                    require(handler.get("type") == "command", f"{host}: expected command hook")
                    script = f"${{{variable}}}/hooks/audit_guard.py"
                    if host == "Claude":
                        require(handler.get("command") == "python3" and handler.get("args") == [script, modes[event]],
                                f"{host}: incorrect shared guard command")
                    else:
                        require(handler.get("command") == f'python3 "{script}" {modes[event]}' and "args" not in handler,
                                f"{host}: incorrect shared guard command")
                    if event in {"PostToolUse", "Stop"}:
                        require(handler.get("timeout", 0) > 12, f"{host}: hook timeout below doctor timeout")
    for relative in (".mcp.json", "mcp/codex.json"):
        servers = read_json(ROOT / relative)["mcpServers"]
        require(set(servers) == {"audit-workflow"}, f"{relative}: unexpected/missing audit server")
        server = servers["audit-workflow"]
        require(server.get("command") == "python3", f"{relative}: expected Python launcher")
        if relative == ".mcp.json":
            require(server.get("args") == ["${CLAUDE_PLUGIN_ROOT}/mcp/audit_mcp_server.py"],
                    "Claude: incorrect shared MCP path")
        else:
            # Native Codex resolves relative cwd from the installed plugin root,
            # but does not interpolate PLUGIN_ROOT in MCP args or env.
            require(server.get("cwd") == ".", "Codex: cwd must resolve to the installed plugin root")
            require(server.get("args") == ["mcp/audit_mcp_server.py"],
                    "Codex: MCP path must be relative to plugin cwd")
        env = server.get("env", {})
        require(env.get("AUDIT_REQUIRE_EXPLICIT_ROOT") == "1" and "AUDIT_PROJECT_DIR" not in env,
                f"{relative}: require explicit project roots, not plugin cwd")
        if relative == "mcp/codex.json":
            require("AUDIT_PLUGIN_ROOT" not in env,
                    "Codex: do not use unexpanded PLUGIN_ROOT in native MCP env")
    for relative in ("scripts/audit.py", "scripts/scatter_scan.py", "hooks/audit_guard.py", "hooks/plugin_root.py", "mcp/audit_mcp_server.py"):
        local_path(relative)
    print("Audit adapters: shared runtime and guard, explicit project roots (host execution not checked)")


def main():
    name, claude, codex = validate_manifests()
    validate_marketplaces(name, codex)
    validate_skills(name)
    validate_files()
    validate_audit_adapters()
    print(f"{name}: package valid")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        raise SystemExit(1)
