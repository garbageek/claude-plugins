#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from plugin_root import plugin_root, project_dir
except Exception:  # pragma: no cover - defensive fallback for hook launch oddities
    def plugin_root() -> Path:
        env = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("AUDIT_PLUGIN_ROOT")
        return Path(env).resolve() if env else Path(__file__).resolve().parents[1]

    def project_dir(payload: dict | None = None) -> Path:
        payload = payload or {}
        env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("AUDIT_PROJECT_DIR")
        if env:
            return Path(env).resolve()
        return Path(payload.get("cwd") or os.getcwd()).resolve()

LIFECYCLE_STATUSES = "PASS|PARTIAL|FAIL|READY_FOR_VERIFICATION|REGRESS|BLOCKED|WONTFIX|INVALID"
STATUS_RE = re.compile(rf"(?:Verification\s+Status|Status)\s*[:=].*(?:{LIFECYCLE_STATUSES})", re.IGNORECASE | re.DOTALL)
MD_STATUS_RE = re.compile(rf"\*\*(?:Verification\s+Status|Status):\*\*\s*`?(?:{LIFECYCLE_STATUSES})`?", re.IGNORECASE)
AUDIT_FILE_RE = re.compile(r"(?:^|[\s'\"])(?:\./)?audit/(?:tickets|verification|triage)/[^\s'\"]+\.md")
DIRECT_MUTATOR_RE = re.compile(r"\b(?:sed|perl|python|python3|ruby|node|awk|ed)\b.*(?:Status|Verification\s+Status).*(?:" + LIFECYCLE_STATUSES + r")", re.IGNORECASE | re.DOTALL)
ALLOWED_AUDIT_CMD_RE = re.compile(r"(^|[;&|\s])(?:python3?\s+[^;&|\n]*bin/audit|audit)\s+(?:verify|resolve|open|update|wontfix|close|reopen|triage|deps)\b", re.IGNORECASE)


def _read_payload() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _tool_input(payload: dict) -> dict:
    for key in ("tool_input", "toolInput", "input", "arguments"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _tool_name(payload: dict) -> str:
    return str(payload.get("tool_name") or payload.get("toolName") or payload.get("name") or "")


def _json_out(obj: dict) -> None:
    print(json.dumps(obj, separators=(",", ":")))


def _deny(reason: str) -> int:
    _json_out({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    })
    return 0


def _context(event: str, text: str) -> int:
    if not text.strip():
        return 0
    _json_out({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text.strip()}})
    return 0


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _file_paths(value) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"file_path", "filePath", "path", "filename"} and isinstance(item, str):
                paths.append(item)
            else:
                paths.extend(_file_paths(item))
    elif isinstance(value, list):
        for item in value:
            paths.extend(_file_paths(item))
    return paths


def _touches_audit_file(tool_input: dict) -> bool:
    paths = _file_paths(tool_input)
    if any("/audit/" in p or p.startswith("audit/") or p.startswith("./audit/") for p in paths):
        return True
    return bool(AUDIT_FILE_RE.search(_as_text(tool_input)))


def _contains_lifecycle_status(tool_input: dict) -> bool:
    text = _as_text(tool_input)
    return bool(STATUS_RE.search(text) or MD_STATUS_RE.search(text))


def _run_audit(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    audit = plugin_root() / "bin" / "audit"
    return subprocess.run(
        [str(audit), "--root", str(project), *args],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def pre_tool_use(payload: dict) -> int:
    tool = _tool_name(payload)
    tin = _tool_input(payload)

    if tool == "Bash":
        command = str(tin.get("command") or "")
        if ALLOWED_AUDIT_CMD_RE.search(command):
            return 0
        if AUDIT_FILE_RE.search(command) and DIRECT_MUTATOR_RE.search(command):
            return _deny(
                "Audit lifecycle statuses must be changed through the audit CLI/MCP runtime, not direct shell rewrites. "
                "Use `audit resolve ... --as audit-resolution` or `audit verify ... --as audit-verification`."
            )
        return 0

    if tool in {"Edit", "Write", "MultiEdit"}:
        if _touches_audit_file(tin) and _contains_lifecycle_status(tin):
            return _deny(
                "Direct edits to audit lifecycle status fields are blocked. Use audit CLI/MCP commands so role, state-machine, and evidence gates run."
            )
    return 0


def post_tool_use(payload: dict) -> int:
    tin = _tool_input(payload)
    if not _touches_audit_file(tin):
        return 0
    project = project_dir(payload)
    if not (project / "audit").exists():
        return 0
    result = _run_audit(project, "doctor")
    if result.returncode == 0:
        return 0
    details = (result.stderr or result.stdout or "audit doctor failed").strip()
    return _context("PostToolUse", "Audit workflow doctor found issues after audit file changes. Prefer fixing via `audit doctor --fix` or lifecycle commands.\n" + details[:4000])


def session_start(payload: dict) -> int:
    project = project_dir(payload)
    if (project / "audit").exists():
        return _context("SessionStart", "Audit Workflow plugin is active for this project. Start with `audit doctor` and `audit summary`; use lifecycle commands for status changes.")
    return _context("SessionStart", "Audit Workflow plugin is available. If this task needs persistent audit tickets, run `audit init` first.")


def stop(payload: dict) -> int:
    project = project_dir(payload)
    if not (project / "audit").exists():
        return 0
    doctor = _run_audit(project, "doctor")
    if doctor.returncode != 0:
        details = (doctor.stderr or doctor.stdout or "audit doctor failed").strip()
        return _context("Stop", "Before finishing, audit workflow health is not clean:\n" + details[:4000])
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    payload = _read_payload()
    if mode == "pre-tool-use":
        return pre_tool_use(payload)
    if mode == "post-tool-use":
        return post_tool_use(payload)
    if mode == "session-start":
        return session_start(payload)
    if mode == "stop":
        return stop(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
