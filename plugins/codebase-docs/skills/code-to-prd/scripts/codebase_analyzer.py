#!/usr/bin/env python3
"""Conservative static inventory for evidence-backed PRD reverse engineering.

The analyzer is package-aware: framework extractors run only inside the nearest
manifest scope and only against receivers/imports that provide evidence for the
framework or HTTP client being reported. Stdlib only.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

IGNORED_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "coverage", "venv", ".venv",
    "__pycache__", ".nuxt", ".output", ".cache", ".turbo", ".vercel", "out",
    "storybook-static", ".tox", ".mypy_cache", ".pytest_cache", "htmlcov", "staticfiles",
    "media", "egg-info",
}
CODE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte", ".astro", ".py"}
COMPONENT_EXTENSIONS = {".tsx", ".jsx", ".vue", ".svelte", ".astro"}
FRAMEWORK_SIGNALS = {
    "react": {"react", "react-dom"}, "next": {"next"}, "vue": {"vue"}, "nuxt": {"nuxt"},
    "angular": {"@angular/core"}, "svelte": {"svelte"}, "sveltekit": {"@sveltejs/kit"},
    "solid": {"solid-js"}, "astro": {"astro"}, "remix": {"@remix-run/react"},
    "nestjs": {"@nestjs/core"}, "express": {"express"}, "fastify": {"fastify"},
}
PYTHON_FRAMEWORKS = {"django", "fastapi", "flask"}
ROUTE_FILE_NAMES = ("router", "routes", "routing")
MOCK_PATTERNS = [re.compile(p, re.I) for p in (
    r"Promise\.resolve\s*\(", r"__mocks__", r"\bmock(?:Data|Response|Result|[A-Z]\w*)\b",
    r"\bfaker\.", r"fixtures?/", r"\.mock\.",
)]


@dataclass(frozen=True)
class Scope:
    root: Path
    manifests: tuple[Path, ...]
    frameworks: frozenset[str]
    name: str
    key_deps: tuple[tuple[str, str], ...] = ()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def walk_files(root: Path, extensions: set[str] = CODE_EXTENSIONS) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix in extensions:
                files.append(p)
    return sorted(files)


def dependency_manifests(root: Path) -> list[Path]:
    names = {"package.json", "requirements.txt", "pyproject.toml", "setup.py", "Pipfile"}
    manifests: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        manifests.extend(Path(dirpath) / name for name in filenames if name in names)
    return sorted(manifests)


def named_directories(root: Path, name: str) -> list[Path]:
    matches: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        if name in dirnames:
            matches.append(Path(dirpath) / name)
    return sorted(matches)


def parse_manifest(manifest: Path) -> tuple[set[str], str | None, dict[str, str]]:
    frameworks: set[str] = set()
    name: str | None = None
    key_deps: dict[str, str] = {}
    try:
        text = manifest.read_text(errors="replace")
    except OSError:
        return frameworks, name, key_deps
    lower = text.lower()
    if manifest.name == "package.json":
        try:
            pkg = json.loads(text)
        except json.JSONDecodeError:
            pkg = {}
        name = str(pkg.get("name")) if pkg.get("name") else None
        deps: dict[str, str] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            deps.update(pkg.get(key, {}) or {})
        for fw, signals in FRAMEWORK_SIGNALS.items():
            if signals & deps.keys():
                frameworks.add(fw)
        for dep, version in deps.items():
            if any(token in dep for token in (
                "router", "redux", "pinia", "zustand", "tanstack", "swr", "axios", "tailwind",
                "material", "prisma", "typeorm", "sequelize", "mongoose", "passport", "jwt",
                "class-validator", "zod",
            )):
                key_deps[dep] = str(version)
    else:
        for fw in PYTHON_FRAMEWORKS:
            if re.search(rf"\b{fw}\b", lower):
                frameworks.add(fw)
    return frameworks, name, key_deps


def discover_scopes(root: Path) -> list[Scope]:
    grouped: dict[Path, list[Path]] = defaultdict(list)
    for manifest in dependency_manifests(root):
        grouped[manifest.parent].append(manifest)
    scopes: list[Scope] = []
    for scope_root, manifests in grouped.items():
        frameworks: set[str] = set()
        names: list[str] = []
        key_deps: dict[str, str] = {}
        for manifest in manifests:
            found, name, deps = parse_manifest(manifest)
            frameworks.update(found)
            if name:
                names.append(name)
            key_deps.update(deps)
        scopes.append(Scope(scope_root, tuple(manifests), frozenset(frameworks), names[0] if len(names) == 1 else scope_root.name, tuple(sorted(key_deps.items()))))
    if not scopes:
        scopes.append(Scope(root, (), frozenset(), root.name))
    return sorted(scopes, key=lambda s: (len(s.root.parts), s.root.as_posix()))


def scope_for_file(path: Path, scopes: list[Scope], project_root: Path) -> Scope:
    candidates = [s for s in scopes if path == s.root or s.root in path.parents]
    if candidates:
        return max(candidates, key=lambda s: len(s.root.parts))
    return Scope(project_root, (), frozenset(), project_root.name)


def detect_frameworks(root: Path, scopes: list[Scope]) -> dict[str, Any]:
    detected = sorted({fw for scope in scopes for fw in scope.frameworks})
    key_deps = dict(pair for scope in scopes for pair in scope.key_deps)
    manifests = [rel(m, root) for scope in scopes for m in scope.manifests]
    names = [scope.name for scope in scopes if scope.name]
    return {
        "framework": detected[0] if len(detected) == 1 else ("multi" if detected else "unknown"),
        "detected_frameworks": detected,
        "name": names[0] if len(names) == 1 else root.name,
        "manifests": manifests,
        "key_deps": key_deps,
        "applications": [
            {"root": rel(s.root, root) or ".", "name": s.name, "frameworks": sorted(s.frameworks), "manifests": [rel(m, root) for m in s.manifests]}
            for s in scopes
        ],
    }


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def normalize_path(path: str) -> str:
    path = path.strip().replace("\\", "/")
    if not path:
        return "/"
    path = re.sub(r"//+", "/", "/" + path.lstrip("/"))
    return path if path == "/" else path.rstrip("/")


def join_paths(*parts: str) -> str:
    return normalize_path("/".join(p.strip("/") for p in parts if p is not None and p != ""))


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def extract_config_frontend_routes(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    patterns = [
        re.compile(r"<Route\b[^>]*\bpath\s*=\s*[\"']([^\"']+)[\"']", re.S),
        re.compile(r"\bpath\s*:\s*[\"']([^\"']+)[\"']"),
    ]
    out = []
    for pattern in patterns:
        for m in pattern.finditer(text):
            value = m.group(1)
            if value.startswith("http") or len(value) > 300:
                continue
            out.append({"path": normalize_path(value), "source": rel(path, root), "line": line_number(text, m.start()), "type": "frontend"})
    return out


def next_app_routes(app_dir: Path, root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    for p in app_dir.rglob("*"):
        if not p.is_file() or p.suffix not in {".js", ".jsx", ".ts", ".tsx"} or p.stem not in {"page", "route"}:
            continue
        segments: list[str] = []
        for segment in p.parent.relative_to(app_dir).parts:
            if segment.startswith("(") and segment.endswith(")"):
                continue
            if segment.startswith("@") or segment.startswith("_"):
                continue
            segment = re.sub(r"^\(\.{1,3}\)", "", segment)
            segment = re.sub(r"^\[\[\.\.\.(\w+)\]\]$", r"*\1?", segment)
            segment = re.sub(r"^\[\.\.\.(\w+)\]$", r"*\1", segment)
            segment = re.sub(r"^\[(\w+)\]$", r":\1", segment)
            if segment:
                segments.append(segment)
        route = normalize_path("/" + "/".join(segments))
        if p.stem == "page":
            pages.append({"path": route, "source": rel(p, root), "filesystem": True, "type": "frontend"})
        else:
            text = read_text(p)
            methods = re.findall(r"(?:export\s+)?(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b|export\s+const\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b", text)
            for method in sorted({a or b for a, b in methods}) or ["UNKNOWN"]:
                endpoints.append({"path": route, "method": method, "source": rel(p, root), "line": 1, "type": "backend", "framework": "next"})
    return pages, endpoints


def pages_dir_routes(pages_dir: Path, root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    endpoints: list[dict[str, Any]] = []
    for p in pages_dir.rglob("*"):
        if not p.is_file() or p.suffix not in {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"}:
            continue
        relative = p.relative_to(pages_dir)
        if p.name.startswith("_") or p.name in {"404.tsx", "404.jsx", "500.tsx", "500.jsx"}:
            continue
        route = "/" + relative.with_suffix("").as_posix()
        route = re.sub(r"/index$", "", route) or "/"
        route = re.sub(r"\[\[\.\.\.(\w+)\]\]", r"*\1?", route)
        route = re.sub(r"\[\.\.\.(\w+)\]", r"*\1", route)
        route = re.sub(r"\[(\w+)\]", r":\1", route)
        item_path = normalize_path(route)
        if relative.parts and relative.parts[0] == "api":
            text = read_text(p)
            methods = set(re.findall(r"\b(?:req|request)\.method\s*===?\s*[\"']([A-Z]+)[\"']", text, re.I))
            methods.update(re.findall(r"\bcase\s+[\"']([A-Z]+)[\"']\s*:", text, re.I))
            for method in sorted(m.upper() for m in methods) or ["UNKNOWN"]:
                endpoints.append({"path": item_path, "method": method, "source": rel(p, root), "line": 1, "type": "backend", "framework": "next"})
        else:
            pages.append({"path": item_path, "source": rel(p, root), "filesystem": True, "type": "frontend"})
    return pages, endpoints


def extract_nest_routes(path: Path, root: Path, global_prefix: str | None = None) -> list[dict[str, Any]]:
    text = read_text(path)
    prefix_match = re.search(r"@Controller\s*\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)", text)
    controller_prefix = prefix_match.group(1) if prefix_match and prefix_match.group(1) else ""
    out = []
    pattern = re.compile(r"@(Get|Post|Put|Delete|Patch|Head|Options|All)\s*\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)")
    for m in pattern.finditer(text):
        item = {
            "path": join_paths(global_prefix or "", controller_prefix, m.group(2) or ""), "method": m.group(1).upper(),
            "source": rel(path, root), "line": line_number(text, m.start()), "type": "backend", "framework": "nestjs",
        }
        if global_prefix is None:
            item["unresolved_prefix"] = True
        out.append(item)
    return out


def js_imported_names(text: str, module: str) -> set[str]:
    names: set[str] = set()
    for m in re.finditer(rf"import\s+([A-Za-z_$][\w$]*)\s+from\s+['\"]{re.escape(module)}['\"]", text):
        names.add(m.group(1))
    for m in re.finditer(rf"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\s*\(\s*['\"]{re.escape(module)}['\"]\s*\)", text):
        names.add(m.group(1))
    return names


def extract_express_fastify_routes(path: Path, root: Path, frameworks: set[str]) -> list[dict[str, Any]]:
    text = read_text(path)
    receivers: dict[str, str] = {}
    express_imports = js_imported_names(text, "express")
    fastify_imports = js_imported_names(text, "fastify")
    for imported in express_imports:
        for m in re.finditer(rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*{re.escape(imported)}\s*\(\s*\)", text):
            receivers[m.group(1)] = "express"
        for m in re.finditer(rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*{re.escape(imported)}\.Router\s*\(\s*\)", text):
            receivers[m.group(1)] = "express"
    if re.search(r"\b(?:const|let|var)\s+router\s*=\s*express\.Router\s*\(", text):
        receivers["router"] = "express"
    for imported in fastify_imports:
        for m in re.finditer(rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*{re.escape(imported)}\s*\(", text):
            receivers[m.group(1)] = "fastify"
    if "fastify" in frameworks and re.search(r"\bfastify\s*\(", text):
        receivers.setdefault("fastify", "fastify")
    out: list[dict[str, Any]] = []
    if not receivers:
        return out
    mounts: dict[str, str] = {}
    for parent in receivers:
        for m in re.finditer(rf"\b{re.escape(parent)}\s*\.\s*(?:use|register)\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([A-Za-z_$][\w$]*)", text):
            mounts[m.group(2)] = m.group(1)
    receiver_pattern = "|".join(re.escape(r) for r in sorted(receivers, key=len, reverse=True))
    pattern = re.compile(rf"\b({receiver_pattern})\s*\.\s*(get|post|put|patch|delete|head|options|all)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
    for m in pattern.finditer(text):
        receiver = m.group(1)
        item = {"path": join_paths(mounts.get(receiver, ""), m.group(3)), "method": m.group(2).upper(), "source": rel(path, root), "line": line_number(text, m.start()), "type": "backend", "framework": receivers[receiver]}
        if receiver not in mounts and receiver not in {"app", "server", "fastify"}:
            item["unresolved_prefix"] = True
        out.append(item)
    return out


def python_assignments(tree: ast.AST) -> dict[str, ast.Call]:
    result: dict[str, ast.Call] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(value, ast.Call):
                for target in targets:
                    if isinstance(target, ast.Name):
                        result[target.id] = value
    return result


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def literal_str(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def extract_fastapi_flask_routes(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    assignments = python_assignments(tree)
    receivers: dict[str, tuple[str, str]] = {}
    for name, call in assignments.items():
        callee = dotted_name(call.func)
        if callee.endswith(("FastAPI", "APIRouter")):
            prefix = next((literal_str(k.value) for k in call.keywords if k.arg == "prefix"), None) or ""
            receivers[name] = ("fastapi", prefix)
        elif callee.endswith(("Flask", "Blueprint")):
            prefix = next((literal_str(k.value) for k in call.keywords if k.arg in {"url_prefix", "prefix"}), None) or ""
            receivers[name] = ("flask", prefix)
    out: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute) or not isinstance(decorator.func.value, ast.Name):
                continue
            receiver = decorator.func.value.id
            if receiver not in receivers:
                continue
            framework, prefix = receivers[receiver]
            route = literal_str(decorator.args[0]) if decorator.args else None
            if route is None:
                continue
            method_name = decorator.func.attr.lower()
            if framework == "fastapi" and method_name in {"get", "post", "put", "patch", "delete", "head", "options", "api_route"}:
                methods = [method_name.upper()]
                if method_name == "api_route":
                    methods = []
                    for kw in decorator.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods = [s for e in kw.value.elts if (s := literal_str(e))]
                    methods = methods or ["UNKNOWN"]
            elif framework == "flask" and method_name == "route":
                methods = ["GET"]
                for kw in decorator.keywords:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        methods = [s for e in kw.value.elts if (s := literal_str(e))] or methods
            else:
                continue
            for method in methods:
                item = {"path": join_paths(prefix, route), "method": method.upper(), "source": rel(path, root), "line": decorator.lineno, "type": "backend", "framework": framework}
                if not prefix and receiver not in {"app"}:
                    item["unresolved_prefix"] = True
                out.append(item)
    return out


def extract_django_routes(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out = []
    for m in re.finditer(r"\b(?:path|re_path|url)\s*\(\s*r?['\"]([^'\"]*)['\"]", text):
        out.append({"path": normalize_path(m.group(1)), "method": "UNKNOWN", "source": rel(path, root), "line": line_number(text, m.start()), "type": "backend", "framework": "django", "unresolved_prefix": "include(" in text[m.start():m.start()+300]})
    for m in re.finditer(r"\.register\s*\(\s*r?['\"]([^'\"]+)['\"]", text):
        out.append({"path": normalize_path(m.group(1)), "method": "RESOURCE", "source": rel(path, root), "line": line_number(text, m.start()), "type": "backend", "framework": "django-rest-framework", "unresolved_prefix": True})
    return out


def extract_outbound_apis(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out: list[dict[str, Any]] = []
    clients: set[str] = set()
    axios_names = js_imported_names(text, "axios")
    clients.update(axios_names)
    for axios_name in axios_names:
        for m in re.finditer(rf"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*{re.escape(axios_name)}\.create\s*\(", text):
            clients.add(m.group(1))
    for m in re.finditer(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*new\s+(?:HttpClient|Axios|Ky)\s*\(", text):
        clients.add(m.group(1))
    if clients:
        receiver_pattern = "|".join(re.escape(c) for c in sorted(clients, key=len, reverse=True))
        pattern = re.compile(rf"\b({receiver_pattern})\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[`'\"]([^`'\"]+)[`'\"]", re.I)
        for m in pattern.finditer(text):
            snippet = text[max(0, m.start()-160):min(len(text), m.end()+160)]
            out.append({"path": m.group(3), "method": m.group(2).upper(), "source": rel(path, root), "line": line_number(text, m.start()), "integrated": True, "mock_detected": any(p.search(snippet) for p in MOCK_PATTERNS), "direction": "outbound"})
    fetch_pattern = re.compile(r"\bfetch\s*\(\s*[`'\"]([^`'\"]+)[`'\"]\s*(?:,\s*\{(.*?)\})?", re.I | re.S)
    for m in fetch_pattern.finditer(text):
        options = m.group(2) or ""
        method_match = re.search(r"\bmethod\s*:\s*['\"]([A-Z]+)['\"]", options, re.I)
        snippet = text[max(0, m.start()-160):min(len(text), m.end()+160)]
        out.append({"path": m.group(1), "method": method_match.group(1).upper() if method_match else "GET", "source": rel(path, root), "line": line_number(text, m.start()), "integrated": True, "mock_detected": any(p.search(snippet) for p in MOCK_PATTERNS), "direction": "outbound"})
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree:
            aliases: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in {"requests", "httpx", "aiohttp"}:
                            aliases.add(alias.asname or alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module in {"requests", "httpx", "aiohttp"}:
                    aliases.add(node.module.split(".")[0])
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                base = dotted_name(node.func.value).split(".")[0]
                if base not in aliases or node.func.attr.lower() not in {"get", "post", "put", "patch", "delete"} or not node.args:
                    continue
                url = literal_str(node.args[0])
                if url is not None:
                    out.append({"path": url, "method": node.func.attr.upper(), "source": rel(path, root), "line": node.lineno, "integrated": True, "mock_detected": False, "direction": "outbound"})
    return out


def class_nodes(text: str) -> Iterable[ast.ClassDef]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def extract_python_models(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out = []
    for node in class_nodes(text):
        bases = [dotted_name(b) or (ast.unparse(b) if hasattr(ast, "unparse") else "") for b in node.bases]
        joined = " ".join(bases)
        framework = "django" if "models.Model" in joined else "pydantic" if "BaseModel" in joined else "sqlalchemy" if re.search(r"\bBase\b|DeclarativeBase", joined) else None
        if not framework:
            continue
        fields = []
        for statement in node.body:  # direct class body only; method locals are excluded
            if framework == "django" and isinstance(statement, (ast.Assign, ast.AnnAssign)):
                target = statement.targets[0] if isinstance(statement, ast.Assign) and statement.targets else statement.target
                value = statement.value
                if isinstance(target, ast.Name) and isinstance(value, ast.Call) and dotted_name(value.func).startswith("models."):
                    fields.append({"name": target.id, "type": dotted_name(value.func).split(".")[-1], "args": ast.unparse(value)[0:300] if hasattr(ast, "unparse") else ""})
            elif framework in {"pydantic", "sqlalchemy"} and isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                fields.append({"name": statement.target.id, "type": ast.unparse(statement.annotation) if hasattr(ast, "unparse") else "", "default": ast.unparse(statement.value)[:200] if statement.value is not None and hasattr(ast, "unparse") else ""})
        out.append({"name": node.name, "qualified_name": f"{rel(path, root)}:{node.name}", "source": rel(path, root), "line": node.lineno, "framework": framework, "fields": fields})
    return out


def extract_ts_models(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out = []
    pattern = re.compile(r"(?:@Entity\s*\([^)]*\)\s*)?(?:export\s+)?class\s+(\w+(?:Dto|DTO|Entity|Schema)?|\w+)\s*\{(.*?)\n\}", re.S)
    for m in pattern.finditer(text):
        block = m.group(2)
        if not ("@Entity" in m.group(0) or re.search(r"(?:Dto|DTO|Entity|Schema)$", m.group(1))):
            continue
        fields = [{"name": fm.group(1), "type": fm.group(2).strip()} for fm in re.finditer(r"(?:@[A-Za-z]+\([^)]*\)\s*)*\s*(\w+)[!?]?\s*:\s*([^;\n]+)", block)]
        out.append({"name": m.group(1), "qualified_name": f"{rel(path, root)}:{m.group(1)}", "source": rel(path, root), "line": line_number(text, m.start()), "framework": "typescript", "fields": fields})
    return out


def extract_enums(path: Path, root: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    out = []
    for m in re.finditer(r"\b(?:export\s+)?(?:const\s+)?enum\s+(\w+)\s*\{(.*?)\}", text, re.S):
        values: dict[str, str] = {}
        next_num = 0
        for raw in re.split(r",(?=(?:[^'\"]|'[^']*'|\"[^\"]*\")*$)", m.group(2)):
            raw = re.sub(r"//.*|/\*.*?\*/", "", raw, flags=re.S).strip()
            mm = re.match(r"(\w+)\s*(?:=\s*(.+))?$", raw, re.S) if raw else None
            if not mm:
                continue
            key, value = mm.group(1), mm.group(2)
            if value is None:
                value = str(next_num); next_num += 1
            else:
                value = value.strip()
                if re.fullmatch(r"-?\d+", value):
                    next_num = int(value) + 1
            values[key] = value
        out.append({"name": m.group(1), "type": "typescript_enum", "values": values, "source": rel(path, root), "line": line_number(text, m.start())})
    if path.suffix == ".py":
        for node in class_nodes(text):
            bases = [dotted_name(b) for b in node.bases]
            if any(re.search(r"(?:Enum|TextChoices|IntegerChoices)$", b) for b in bases):
                values = {}
                for statement in node.body:
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name) and hasattr(ast, "unparse"):
                        values[statement.targets[0].id] = ast.unparse(statement.value)
                out.append({"name": node.name, "type": "python_enum", "values": values, "source": rel(path, root), "line": node.lineno})
    return out


def dedupe(items: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen = set(); out = []
    for item in items:
        key = tuple(item.get(k) for k in key_fields)
        if key not in seen:
            seen.add(key); out.append(item)
    return out


def nest_global_prefix(scope: Scope) -> str | None:
    for path in walk_files(scope.root, {".ts", ".js"}):
        text = read_text(path)
        m = re.search(r"\.setGlobalPrefix\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", text)
        if m:
            return m.group(1)
    return None


def analyze_project(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    if not root.is_dir():
        return {"error": f"Not a directory: {root}"}
    scopes = discover_scopes(root)
    framework_info = detect_frameworks(root, scopes)
    files = walk_files(root)
    frontend: list[dict[str, Any]] = []
    backend: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    enums: list[dict[str, Any]] = []
    models: list[dict[str, Any]] = []
    nest_prefixes = {s.root: nest_global_prefix(s) for s in scopes if "nestjs" in s.frameworks}

    for f in files:
        scope = scope_for_file(f, scopes, root)
        frameworks = set(scope.frameworks)
        low = f.name.lower()
        if any(token in low for token in ROUTE_FILE_NAMES) and frameworks & {"react", "vue", "angular", "svelte", "solid", "remix"}:
            frontend.extend(extract_config_frontend_routes(f, root))
        if "nestjs" in frameworks and ".controller." in low:
            backend.extend(extract_nest_routes(f, root, nest_prefixes.get(scope.root)))
        if frameworks & {"express", "fastify"} and f.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            backend.extend(extract_express_fastify_routes(f, root, frameworks))
        if f.suffix == ".py":
            if frameworks & {"fastapi", "flask"}:
                backend.extend(extract_fastapi_flask_routes(f, root))
            if "django" in frameworks and f.name == "urls.py":
                backend.extend(extract_django_routes(f, root))
            models.extend(extract_python_models(f, root))
        else:
            models.extend(extract_ts_models(f, root))
        outbound.extend(extract_outbound_apis(f, root))
        enums.extend(extract_enums(f, root))

    for scope in scopes:
        if "next" not in scope.frameworks:
            continue
        for app_dir in named_directories(scope.root, "app"):
            if any(p.name.startswith("page.") for p in app_dir.rglob("page.*")) or any(p.name.startswith("route.") for p in app_dir.rglob("route.*")):
                pages, endpoints = next_app_routes(app_dir, root); frontend.extend(pages); backend.extend(endpoints)
        for pages_dir in named_directories(scope.root, "pages"):
            pages, endpoints = pages_dir_routes(pages_dir, root); frontend.extend(pages); backend.extend(endpoints)

    frontend = sorted(dedupe(frontend, ("path", "source")), key=lambda x: (x["path"], x["source"]))
    backend = sorted(dedupe(backend, ("method", "path", "source")), key=lambda x: (x["path"], x.get("method", ""), x["source"]))
    outbound = sorted(dedupe(outbound, ("method", "path", "source", "line")), key=lambda x: (x["path"], x["source"], x["line"]))
    enums = sorted(dedupe(enums, ("name", "source", "line")), key=lambda x: (x["name"], x["source"]))
    models = sorted(dedupe(models, ("qualified_name",)), key=lambda x: x["qualified_name"])
    stack_type = "fullstack" if frontend and backend else "frontend" if frontend else "backend" if backend else "unknown"
    components = defaultdict(int)
    for f in files:
        components["components" if f.suffix in COMPONENT_EXTENSIONS else "modules"] += 1

    unresolved = sum(bool(e.get("unresolved_prefix")) for e in backend)
    return {
        "project": {
            "root": ".", "name": framework_info["name"], "framework": framework_info["framework"],
            "detected_frameworks": framework_info["detected_frameworks"], "manifests": framework_info["manifests"],
            "applications": framework_info["applications"], "key_dependencies": framework_info["key_deps"], "stack_type": stack_type,
        },
        "structure": {"total_files": len(files), "components": dict(components)},
        "routes": {"count": len(frontend) + len(backend), "frontend_pages": frontend, "backend_endpoints": backend, "pages": frontend, "unresolved_prefixes": unresolved},
        "apis": {"total": len(outbound), "integrated": sum(bool(a["integrated"]) for a in outbound), "mock": sum(bool(a["mock_detected"]) for a in outbound), "endpoints": outbound},
        "enums": {"count": len(enums), "definitions": enums},
        "models": {"count": len(models), "definitions": models},
        "summary": {"pages": len(frontend), "backend_endpoints": len(backend), "api_endpoints": len(outbound), "api_integrated": sum(bool(a["integrated"]) for a in outbound), "api_mock": sum(bool(a["mock_detected"]) for a in outbound), "enums": len(enums), "models": len(models), "unresolved_prefixes": unresolved, "stack_type": stack_type},
        "limitations": [
            "integrated and mock_detected are static client-call/nearby-text signals, not observed live integration or a verified mock implementation.",
            "Entries marked unresolved_prefix require manual composition review before they are treated as full runtime paths.",
            "Django include() prefixes, DRF-generated actions, Express router mounts, and some framework module composition require manual resolution.",
            "Static extraction cannot prove runtime-only routes, permissions, validation, middleware order, or environment behavior; verify these during the manual PRD pass.",
        ],
    }


def markdown_summary(data: dict[str, Any]) -> str:
    p, s = data["project"], data["summary"]
    return "\n".join([
        f"# Codebase Analysis: {p['name']}", "", f"- Frameworks: {', '.join(p['detected_frameworks']) or 'unknown'}",
        f"- Applications/packages: {len(p.get('applications', []))}", f"- Stack: {p['stack_type']}",
        f"- Frontend pages: {s['pages']}", f"- Backend endpoints: {s['backend_endpoints']}",
        f"- Unresolved route prefixes: {s.get('unresolved_prefixes', 0)}", f"- Outbound APIs: {s['api_endpoints']}",
        f"- Models: {s['models']}", f"- Enums: {s['enums']}",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Repository or application directory to inventory")
    parser.add_argument("-o", "--output", help="Explicit inventory output file; otherwise stdout")
    parser.add_argument("-f", "--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    try:
        data = analyze_project(Path(args.project))
        if "error" in data:
            raise ValueError(data["error"])
        rendered = markdown_summary(data) if args.format == "markdown" else json.dumps(data, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, ValueError) as exc:
        print(f"codebase-analyzer: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
