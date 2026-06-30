#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SERVER_NAME = "audit-workflow"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2025-03-26"


def plugin_root() -> Path:
    env = os.environ.get("AUDIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def default_root(args: dict[str, Any] | None = None) -> Path:
    args = args or {}
    value = args.get("root") or os.environ.get("AUDIT_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(value).expanduser().resolve() if value else Path.cwd().resolve()


def audit_bin() -> Path:
    return plugin_root() / "bin" / "audit"


def respond(msg_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
    if msg_id is None:
        return
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    print(json.dumps(payload, separators=(",", ":")), flush=True)


def tool_result(data: Any, *, is_error: bool = False) -> dict[str, Any]:
    text = data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False)
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def run_audit(args: dict[str, Any], *cmd: str, json_mode: bool = True) -> dict[str, Any]:
    root = default_root(args)
    argv = [str(audit_bin()), "--root", str(root), *cmd]
    if json_mode and "--json" not in argv:
        argv.append("--json")
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    except Exception as exc:  # noqa: BLE001 - tool boundary
        return {"ok": False, "command": argv, "error": str(exc)}
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    parsed: Any = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = stdout
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "root": str(root),
        "command": argv,
        "stdout": parsed,
        "stderr": stderr,
    }


def arr(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    return [str(value)] if str(value) else []


def optional_arg(out: list[str], flag: str, value: Any) -> None:
    if value is not None and str(value) != "":
        out.extend([flag, str(value)])


def repeated_arg(out: list[str], flag: str, values: Any) -> None:
    for value in arr(values):
        out.extend([flag, value])


def tools() -> list[dict[str, Any]]:
    str_schema = {"type": "string"}
    root_prop = {"root": {"type": "string", "description": "Project root. Defaults to CLAUDE_PROJECT_DIR or current directory."}}
    return [
        {
            "name": "audit_init",
            "description": "Initialize the audit workflow in a project.",
            "inputSchema": {"type": "object", "properties": root_prop, "additionalProperties": False},
        },
        {
            "name": "audit_doctor",
            "description": "Check audit workflow health.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "fix": {"type": "boolean"}, "strict": {"type": "boolean"}}, "additionalProperties": False},
        },
        {
            "name": "audit_summary",
            "description": "Return audit status summary.",
            "inputSchema": {"type": "object", "properties": root_prop, "additionalProperties": False},
        },
        {
            "name": "audit_next",
            "description": "Return the next ticket for resolution or verification.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "for_role": {"type": "string", "enum": ["resolution", "verification"]}, "category": str_schema, "severity": str_schema}, "required": ["for_role"], "additionalProperties": False},
        },
        {
            "name": "audit_create",
            "description": "Create a DRAFT/OPEN audit ticket from concrete evidence.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "category": str_schema, "title": str_schema, "severity": str_schema, "module": str_schema, "description": str_schema, "evidence": {"type": "array", "items": str_schema}, "acceptance_criteria": {"type": "array", "items": str_schema}, "suggested_verification": str_schema, "open": {"type": "boolean"}}, "required": ["category", "title", "severity"], "additionalProperties": False},
        },
        {
            "name": "audit_resolve",
            "description": "Move ticket(s) to READY_FOR_VERIFICATION with resolution evidence.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": str_schema, "ids": {"type": "array", "items": str_schema}, "fix_commit": str_schema, "evidence": {"type": "array", "items": str_schema}, "test": str_schema, "changed": {"type": "array", "items": str_schema}, "verdict": str_schema}, "required": ["fix_commit", "evidence", "test"], "additionalProperties": False},
        },
        {
            "name": "audit_verify",
            "description": "Write independent verification verdict for ticket(s).",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": str_schema, "ids": {"type": "array", "items": str_schema}, "status": str_schema, "verified_commit": str_schema, "criteria": {"type": "array", "items": str_schema}, "evidence": {"type": "array", "items": str_schema}, "test": str_schema, "verdict": str_schema, "reason": str_schema}, "required": ["status"], "additionalProperties": False},
        },
        {
            "name": "audit_export",
            "description": "Export canonical ticket records as JSON.",
            "inputSchema": {"type": "object", "properties": root_prop, "additionalProperties": False},
        },
    ]


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "audit_init":
        return tool_result(run_audit(args, "init"))
    if name == "audit_doctor":
        cmd = ["doctor"]
        if args.get("fix"):
            cmd.append("--fix")
        if args.get("strict"):
            cmd.append("--strict")
        # doctor has no --json in current CLI; keep text but wrap it.
        return tool_result(run_audit(args, *cmd, json_mode=False))
    if name == "audit_summary":
        return tool_result(run_audit(args, "summary"))
    if name == "audit_next":
        cmd = ["next", "--for", str(args.get("for_role") or "resolution")]
        optional_arg(cmd, "--category", args.get("category"))
        optional_arg(cmd, "--severity", args.get("severity"))
        return tool_result(run_audit(args, *cmd))
    if name == "audit_create":
        # Smooth cold-start: make sure the directory exists before creating.
        run_audit(args, "init")
        cmd = ["create", str(args["category"]), "--title", str(args["title"]), "--severity", str(args["severity"])]
        optional_arg(cmd, "--module", args.get("module"))
        optional_arg(cmd, "--description", args.get("description"))
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        repeated_arg(cmd, "--acceptance-criterion", args.get("acceptance_criteria"))
        optional_arg(cmd, "--suggested-verification", args.get("suggested_verification"))
        if args.get("open"):
            cmd.append("--open")
        return tool_result(run_audit(args, *cmd))
    if name == "audit_resolve":
        ids = arr(args.get("ids")) or arr(args.get("id"))
        cmd = ["resolve", *ids, "--fix-commit", str(args["fix_commit"]), "--test", str(args["test"]), "--as", "audit-resolution"]
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        repeated_arg(cmd, "--changed", args.get("changed"))
        optional_arg(cmd, "--verdict", args.get("verdict"))
        return tool_result(run_audit(args, *cmd))
    if name == "audit_verify":
        ids = arr(args.get("ids")) or arr(args.get("id"))
        cmd = ["verify", *ids, "--status", str(args["status"]), "--as", "audit-verification"]
        optional_arg(cmd, "--verified-commit", args.get("verified_commit"))
        repeated_arg(cmd, "--criterion", args.get("criteria"))
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        optional_arg(cmd, "--test", args.get("test"))
        optional_arg(cmd, "--verdict", args.get("verdict"))
        optional_arg(cmd, "--reason", args.get("reason"))
        return tool_result(run_audit(args, *cmd))
    if name == "audit_export":
        return tool_result(run_audit(args, "export"))
    return tool_result({"ok": False, "error": f"unknown tool: {name}"}, is_error=True)


def handle(msg: dict[str, Any]) -> None:
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    try:
        if method == "initialize":
            client_version = params.get("protocolVersion") if isinstance(params, dict) else None
            respond(msg_id, {
                "protocolVersion": client_version or PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        elif method == "tools/list":
            respond(msg_id, {"tools": tools()})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            respond(msg_id, call_tool(str(name), args if isinstance(args, dict) else {}))
        elif method in {"ping", "notifications/initialized"}:
            if msg_id is not None:
                respond(msg_id, {})
        elif method in {"resources/list", "prompts/list"}:
            key = "resources" if method == "resources/list" else "prompts"
            respond(msg_id, {key: []})
        else:
            respond(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})
    except Exception as exc:  # noqa: BLE001 - protocol boundary
        respond(msg_id, error={"code": -32603, "message": str(exc)})


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            respond(None, error={"code": -32700, "message": str(exc)})
            continue
        if isinstance(msg, list):
            for item in msg:
                if isinstance(item, dict):
                    handle(item)
        elif isinstance(msg, dict):
            handle(msg)


if __name__ == "__main__":
    main()
