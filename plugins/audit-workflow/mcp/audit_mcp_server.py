#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SERVER_NAME = "audit-workflow"
SERVER_VERSION = "1.1.1"
# structuredContent in tool results is defined from 2025-06-18; older clients ignore it.
PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {PROTOCOL_VERSION, "2025-03-26"}


def plugin_root() -> Path:
    env = os.environ.get("AUDIT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def default_root(args: dict[str, Any] | None = None) -> Path:
    args = args or {}
    value = args.get("root") or os.environ.get("AUDIT_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(value).expanduser().resolve() if value else Path.cwd().resolve()


def audit_script() -> Path:
    return plugin_root() / "scripts" / "audit.py"


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
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}], "isError": is_error}
    if isinstance(data, (dict, list)):
        result["structuredContent"] = data
    return result


def audit_tool_result(data: dict[str, Any]) -> dict[str, Any]:
    return tool_result(data, is_error=not bool(data.get("ok", False)))


def run_audit(args: dict[str, Any], *cmd: str, json_mode: bool = True) -> dict[str, Any]:
    root = default_root(args)
    argv = [sys.executable, str(audit_script()), "--root", str(root), *cmd]
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


def parse_doctor_output(stdout: Any, stderr: str = "") -> dict[str, Any]:
    text = stdout if isinstance(stdout, str) else "" if stdout is None else json.dumps(stdout, ensure_ascii=False)
    lines = text.splitlines()
    fixed: list[str] = []
    issues: list[str] = []
    warnings: list[str] = []
    section = ""
    issue_count: int | None = None
    warning_count: int | None = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("FIXED:"):
            fixed.append(stripped.removeprefix("FIXED:").strip())
            continue
        m = re.match(r"Found\s+(\d+)\s+issue\(s\):", stripped)
        if m:
            issue_count = int(m.group(1))
            section = "issues"
            continue
        m = re.match(r"Warnings\s+\((\d+)\):", stripped)
        if m:
            warning_count = int(m.group(1))
            section = "warnings"
            continue
        if stripped.startswith("- "):
            if section == "issues":
                issues.append(stripped[2:].strip())
            elif section == "warnings":
                warnings.append(stripped[2:].strip())

    return {
        "healthy": "Audit directory is healthy." in text and issue_count in {None, 0},
        "fixed": fixed,
        "issues": issues,
        "issue_count": len(issues) if issue_count is None else issue_count,
        "warnings": warnings,
        "warning_count": len(warnings) if warning_count is None else warning_count,
        "stdout_text": text,
        "stderr": stderr,
    }


def run_doctor(args: dict[str, Any], *, fix: bool = False, strict: bool = False) -> dict[str, Any]:
    cmd = ["doctor"]
    if fix:
        cmd.append("--fix")
    if strict:
        cmd.append("--strict")

    first = run_audit(args, *cmd, json_mode=False)
    first_parsed = parse_doctor_output(first.get("stdout"), str(first.get("stderr") or ""))

    if not fix:
        return {
            "ok": bool(first.get("ok")),
            "returncode": first.get("returncode"),
            "root": first.get("root"),
            "command": first.get("command"),
            "doctor": first_parsed,
            "stderr": first.get("stderr", ""),
        }

    recheck_cmd = ["doctor"]
    if strict:
        recheck_cmd.append("--strict")
    recheck = run_audit(args, *recheck_cmd, json_mode=False)
    recheck_parsed = parse_doctor_output(recheck.get("stdout"), str(recheck.get("stderr") or ""))

    return {
        "ok": bool(recheck.get("ok")),
        "returncode": recheck.get("returncode"),
        "root": recheck.get("root"),
        "command": first.get("command"),
        "recheck_command": recheck.get("command"),
        "rechecked_after_fix": True,
        "fix_attempt": first_parsed,
        "doctor": recheck_parsed,
        "stderr": recheck.get("stderr", ""),
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
    id_schema = {"type": "string", "pattern": r"^\d+$"}
    root_prop = {"root": {"type": "string", "description": "Project root. Defaults to CLAUDE_PROJECT_DIR or current directory."}}
    category_schema = {"type": "string", "enum": ["BUG", "DEGRADED", "LOST", "TODO", "TEST", "CONFIG", "SECURITY", "CODE-QUALITY"]}
    severity_schema = {"type": "string", "enum": ["critical", "high", "medium", "low"]}
    verification_status_schema = {"type": "string", "enum": ["PASS", "PARTIAL", "FAIL", "REGRESS", "BLOCKED", "WONTFIX", "INVALID"]}
    return [
        {
            "name": "audit_init",
            "description": "Initialize the audit workflow in a project.",
            "inputSchema": {"type": "object", "properties": root_prop, "additionalProperties": False},
        },
        {
            "name": "audit_doctor",
            "description": "Check audit workflow health. With fix=true, apply supported fixes and return a fresh re-check result.",
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
            "inputSchema": {"type": "object", "properties": {**root_prop, "for_role": {"type": "string", "enum": ["resolution", "verification"]}, "category": category_schema, "severity": severity_schema}, "required": ["for_role"], "additionalProperties": False},
        },
        {
            "name": "audit_show",
            "description": "Show the ticket and verification record for one or more IDs.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "ids": {"type": "array", "items": id_schema}}, "additionalProperties": False},
        },
        {
            "name": "audit_create",
            "description": "Initialize the audit workflow when needed, then create a DRAFT/OPEN audit ticket from concrete evidence.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "category": category_schema, "title": str_schema, "severity": severity_schema, "module": str_schema, "lines": str_schema, "source": str_schema, "depends_on": {"type": "array", "items": id_schema}, "blocks": {"type": "array", "items": id_schema}, "description": str_schema, "expected": str_schema, "actual": str_schema, "evidence": {"type": "array", "items": str_schema}, "recommendation": str_schema, "acceptance_criteria": {"type": "array", "items": str_schema}, "suggested_verification": str_schema, "open": {"type": "boolean"}}, "required": ["category", "title", "severity"], "additionalProperties": False},
        },
        {
            "name": "audit_open",
            "description": "Promote evidence-ready DRAFT ticket(s) to OPEN as audit-discovery.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "ids": {"type": "array", "items": id_schema}, "verdict": str_schema}, "additionalProperties": False},
        },
        {
            "name": "audit_resolve",
            "description": "Move ticket(s) to READY_FOR_VERIFICATION with resolution evidence.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "ids": {"type": "array", "items": id_schema}, "fix_commit": str_schema, "evidence": {"type": "array", "items": str_schema}, "test": str_schema, "changed": {"type": "array", "items": str_schema}, "verdict": str_schema}, "required": ["fix_commit", "evidence", "test"], "additionalProperties": False},
        },
        {
            "name": "audit_verify",
            "description": "Write independent verification verdict for ticket(s).",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "ids": {"type": "array", "items": id_schema}, "status": verification_status_schema, "verified_commit": str_schema, "criteria": {"type": "array", "items": str_schema}, "evidence": {"type": "array", "items": str_schema}, "test": str_schema, "verdict": str_schema, "reason": str_schema}, "required": ["status"], "additionalProperties": False},
        },
        {
            "name": "audit_triage_set",
            "description": "Set executable triage metadata for one ticket.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "impact": {"type": "integer", "minimum": 1, "maximum": 5}, "effort": {"type": "integer", "minimum": 1, "maximum": 5}, "p_level": {"type": "string", "enum": ["P0", "P1", "P2", "P3"]}, "decision": {"type": "string", "enum": ["FIX", "DEFER", "WONTFIX", "DUPLICATE"]}, "phase": str_schema}, "required": ["id"], "additionalProperties": False},
        },
        {
            "name": "audit_dependency_add",
            "description": "Add canonical dependency edges and update both sides under the audit mutation lock.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "depends_on": {"type": "array", "items": id_schema}, "blocks": {"type": "array", "items": id_schema}}, "required": ["id"], "additionalProperties": False},
        },
        {
            "name": "audit_dependency_remove",
            "description": "Remove canonical dependency edges and update both sides under the audit mutation lock.",
            "inputSchema": {"type": "object", "properties": {**root_prop, "id": id_schema, "depends_on": {"type": "array", "items": id_schema}, "blocks": {"type": "array", "items": id_schema}}, "required": ["id"], "additionalProperties": False},
        },
        {
            "name": "audit_export",
            "description": "Export canonical ticket records as JSON.",
            "inputSchema": {"type": "object", "properties": root_prop, "additionalProperties": False},
        },
    ]


def _ids(args: dict[str, Any]) -> list[str]:
    return arr(args.get("ids")) or arr(args.get("id"))


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "audit_init":
        return audit_tool_result(run_audit(args, "init"))
    if name == "audit_doctor":
        return audit_tool_result(run_doctor(args, fix=bool(args.get("fix")), strict=bool(args.get("strict"))))
    if name == "audit_summary":
        return audit_tool_result(run_audit(args, "summary"))
    if name == "audit_next":
        cmd = ["next", "--for", str(args.get("for_role") or "resolution")]
        optional_arg(cmd, "--category", args.get("category"))
        optional_arg(cmd, "--severity", args.get("severity"))
        return audit_tool_result(run_audit(args, *cmd))
    if name == "audit_show":
        ids = _ids(args)
        if not ids:
            return tool_result({"ok": False, "error": "id or ids is required"}, is_error=True)
        return audit_tool_result(run_audit(args, "show", *ids, json_mode=False))
    if name == "audit_create":
        init_result = run_audit(args, "init")
        if not init_result.get("ok"):
            return audit_tool_result({"ok": False, "stage": "init", "init": init_result})
        cmd = ["create", str(args["category"]), "--title", str(args["title"]), "--severity", str(args["severity"])]
        optional_arg(cmd, "--module", args.get("module"))
        optional_arg(cmd, "--lines", args.get("lines"))
        optional_arg(cmd, "--source", args.get("source"))
        repeated_arg(cmd, "--depends-on", args.get("depends_on"))
        repeated_arg(cmd, "--blocks", args.get("blocks"))
        optional_arg(cmd, "--description", args.get("description"))
        optional_arg(cmd, "--expected", args.get("expected"))
        optional_arg(cmd, "--actual", args.get("actual"))
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        optional_arg(cmd, "--recommendation", args.get("recommendation"))
        repeated_arg(cmd, "--acceptance-criterion", args.get("acceptance_criteria"))
        optional_arg(cmd, "--suggested-verification", args.get("suggested_verification"))
        if args.get("open"):
            cmd.append("--open")
        create_result = run_audit(args, *cmd)
        return audit_tool_result({
            "ok": bool(init_result.get("ok")) and bool(create_result.get("ok")),
            "root": create_result.get("root") or init_result.get("root"),
            "initialized": init_result,
            "created": create_result,
        })
    if name == "audit_open":
        ids = _ids(args)
        if not ids:
            return tool_result({"ok": False, "error": "id or ids is required"}, is_error=True)
        cmd = ["open", *ids, "--as", "audit-discovery"]
        optional_arg(cmd, "--verdict", args.get("verdict"))
        return audit_tool_result(run_audit(args, *cmd))
    if name == "audit_resolve":
        ids = _ids(args)
        if not ids:
            return tool_result({"ok": False, "error": "id or ids is required"}, is_error=True)
        cmd = ["resolve", *ids, "--fix-commit", str(args["fix_commit"]), "--test", str(args["test"]), "--as", "audit-resolution"]
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        repeated_arg(cmd, "--changed", args.get("changed"))
        optional_arg(cmd, "--verdict", args.get("verdict"))
        return audit_tool_result(run_audit(args, *cmd))
    if name == "audit_verify":
        ids = _ids(args)
        if not ids:
            return tool_result({"ok": False, "error": "id or ids is required"}, is_error=True)
        cmd = ["verify", *ids, "--status", str(args["status"]), "--as", "audit-verification"]
        optional_arg(cmd, "--verified-commit", args.get("verified_commit"))
        repeated_arg(cmd, "--criterion", args.get("criteria"))
        repeated_arg(cmd, "--evidence", args.get("evidence"))
        optional_arg(cmd, "--test", args.get("test"))
        optional_arg(cmd, "--verdict", args.get("verdict"))
        optional_arg(cmd, "--reason", args.get("reason"))
        return audit_tool_result(run_audit(args, *cmd))
    if name == "audit_triage_set":
        cmd = ["triage", "set", str(args["id"])]
        optional_arg(cmd, "--impact", args.get("impact"))
        optional_arg(cmd, "--effort", args.get("effort"))
        optional_arg(cmd, "--p-level", args.get("p_level"))
        optional_arg(cmd, "--decision", args.get("decision"))
        optional_arg(cmd, "--phase", args.get("phase"))
        return audit_tool_result(run_audit(args, *cmd, json_mode=False))
    if name in {"audit_dependency_add", "audit_dependency_remove"}:
        action = "add" if name.endswith("_add") else "remove"
        cmd = ["deps", action, str(args["id"])]
        repeated_arg(cmd, "--depends-on", args.get("depends_on"))
        repeated_arg(cmd, "--blocks", args.get("blocks"))
        return audit_tool_result(run_audit(args, *cmd, json_mode=False))
    if name == "audit_export":
        return audit_tool_result(run_audit(args, "export"))
    return tool_result({"ok": False, "error": f"unknown tool: {name}"}, is_error=True)


def handle(msg: dict[str, Any]) -> None:
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params") or {}
    try:
        if method == "initialize":
            client_version = params.get("protocolVersion") if isinstance(params, dict) else None
            selected_version = client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
            respond(msg_id, {
                "protocolVersion": selected_version,
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
