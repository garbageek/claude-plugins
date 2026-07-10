#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

CONSTANT_NAMES = (
    "VALID_CATEGORIES",
    "VALID_SEVERITIES",
    "VALID_STATUSES",
    "VERIFICATION_STATUSES",
    "ACTOR_ROLES",
    "ALLOWED_TRANSITIONS",
)


def _literal(node: ast.AST) -> Any:
    value = ast.literal_eval(node)
    return _normalize(value)


def _normalize(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return [_normalize(v) for v in value]
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    return value


def _assigned_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _assigned_value(node: ast.stmt) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def _module_constants(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, Any] = {}
    for node in tree.body:
        name = _assigned_name(node)
        value = _assigned_value(node)
        if name in CONSTANT_NAMES and value is not None:
            found[name] = _literal(value)
    return found


def _bin_fallback_constants(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            if not _is_module_not_found_handler(handler):
                continue
            for stmt in handler.body:
                name = _assigned_name(stmt)
                value = _assigned_value(stmt)
                if name in CONSTANT_NAMES and value is not None:
                    found[name] = _literal(value)
    return found


def _is_module_not_found_handler(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return False
    if isinstance(handler.type, ast.Name):
        return handler.type.id == "ModuleNotFoundError"
    return False


def compare(plugin_root: Path) -> dict[str, Any]:
    audit_lib = plugin_root / "scripts" / "audit_lib.py"
    audit_bin = plugin_root / "bin" / "audit"
    left = _module_constants(audit_lib)
    right = _bin_fallback_constants(audit_bin)

    missing_in_lib = [name for name in CONSTANT_NAMES if name not in left]
    missing_in_bin = [name for name in CONSTANT_NAMES if name not in right]
    mismatched = []
    for name in CONSTANT_NAMES:
        if name in left and name in right and left[name] != right[name]:
            mismatched.append({"name": name, "audit_lib": left[name], "bin_fallback": right[name]})

    return {
        "ok": not missing_in_lib and not missing_in_bin and not mismatched,
        "audit_lib": str(audit_lib),
        "bin_audit": str(audit_bin),
        "checked": list(CONSTANT_NAMES),
        "missing_in_audit_lib": missing_in_lib,
        "missing_in_bin_fallback": missing_in_bin,
        "mismatched": mismatched,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check audit_lib.py and bin/audit fallback workflow constants for parity.")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = compare(args.plugin_root.resolve())
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif result["ok"]:
        print("audit runtime contract parity: ok")
    else:
        print("audit runtime contract parity: failed")
        for key in ("missing_in_audit_lib", "missing_in_bin_fallback"):
            if result[key]:
                print(f"{key}: {', '.join(result[key])}")
        for item in result["mismatched"]:
            print(f"mismatch: {item['name']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
