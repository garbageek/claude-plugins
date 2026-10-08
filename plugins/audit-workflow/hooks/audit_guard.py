#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from plugin_root import plugin_root, project_dir

LIFECYCLE_STATUSES = "PASS|PARTIAL|FAIL|READY_FOR_VERIFICATION|REGRESS|BLOCKED|WONTFIX|INVALID"
AUDIT_MARKDOWN_PATH = r"(?:\.[\\/])?audit[\\/](?:tickets|verification|triage)[\\/][^\s'\";&|<>]+\.md"
STATUS_RE = re.compile(rf"(?:Verification\s+Status|Status)\s*[:=].*(?:{LIFECYCLE_STATUSES})", re.IGNORECASE | re.DOTALL)
MD_STATUS_RE = re.compile(rf"\*\*(?:Verification\s+Status|Status):\*\*\s*`?(?:{LIFECYCLE_STATUSES})`?", re.IGNORECASE)
AUDIT_FILE_RE = re.compile(rf"(?:^|[\s'\"<>=|&;]){AUDIT_MARKDOWN_PATH}")
AUDIT_MARKDOWN_PATH_RE = re.compile(AUDIT_MARKDOWN_PATH, re.IGNORECASE)
DIRECT_MUTATOR_RE = re.compile(r"\b(?:sed|perl|python|python3|ruby|node|awk|ed)\b.*(?:Status|Verification\s+Status).*(?:" + LIFECYCLE_STATUSES + r")", re.IGNORECASE | re.DOTALL)
INDIRECT_AUDIT_WRITE_RE = re.compile(
    rf"(?:"
    rf"\b(?:mv|cp|tee|install|rsync|dd|truncate)\b[^\n;&|]*{AUDIT_MARKDOWN_PATH}"
    rf"|(?:>|>>)\s*{AUDIT_MARKDOWN_PATH}"
    rf")",
    re.IGNORECASE | re.DOTALL,
)
POWERSHELL_AUDIT_WRITE_RE = re.compile(
    rf"(?:"
    rf"\b(?:Set-Content|Add-Content|Out-File|Move-Item|Copy-Item|Rename-Item)\b[^\n;|]*{AUDIT_MARKDOWN_PATH}"
    rf"|{AUDIT_MARKDOWN_PATH}[^\n;|]*(?:-replace|Set-Content|Add-Content|Out-File)"
    rf")",
    re.IGNORECASE | re.DOTALL,
)


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
    if event == "Stop":
        _json_out({"systemMessage": text.strip()})
    else:
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
    paths = [p.replace("\\", "/") for p in _file_paths(tool_input)]
    if any("/audit/" in p or p.startswith("audit/") or p.startswith("./audit/") for p in paths):
        return True
    return bool(AUDIT_MARKDOWN_PATH_RE.search(_as_text(tool_input)))


def _contains_lifecycle_status(tool_input: dict) -> bool:
    text = _as_text(tool_input)
    return bool(STATUS_RE.search(text) or MD_STATUS_RE.search(text))


# A segment that runs the bundled runtime (`python3 ".../scripts/audit.py" verify ...`)
# is the sanctioned write path. Its quoted arguments may legitimately mention audit
# paths and status words, e.g. `--evidence "see audit/tickets/001-BUG-x.md"`.
RUNTIME_SEGMENT_RE = re.compile(
    r"""^\s*(?:&\s*)?(?:python(?:3(?:\.\d+)?)?(?:\.exe)?|py(?:\.exe)?(?:\s+-3)?)(?:\s+-[IBEsSuO]+)*\s+"""
    r"""(?:"(?:[^"]*[\\/])?scripts[\\/]audit\.py"|'(?:[^']*[\\/])?scripts[\\/]audit\.py'|(?:\S*[\\/])?scripts[\\/]audit\.py)(?=\s|$)""",
    re.IGNORECASE,
)
QUOTED_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'')


def _shell_segments(command: str) -> list[str]:
    """Split on unquoted ;, &, |, and newlines; quoted text stays in its segment."""
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            current.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                current.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
            current.append(ch)
        elif ch in ";&|\n":
            segments.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    segments.append("".join(current))
    return [seg for seg in segments if seg.strip()]


def _segment_writes_audit(segment: str, tool: str) -> bool:
    if RUNTIME_SEGMENT_RE.match(segment):
        # Only unquoted shell syntax (a redirect into an audit file) can turn a
        # runtime call into a direct write; quoted arguments are data.
        def mask_argument(match: re.Match) -> str:
            # A quoted redirection destination is still a file target, not CLI data.
            if re.search(r">\s*$", segment[:match.start()]):
                return match.group(0)[1:-1]
            return '""'

        segment = QUOTED_RE.sub(mask_argument, segment)
        return bool(re.search(rf"(?:>|>>)\s*{AUDIT_MARKDOWN_PATH}", segment, re.IGNORECASE))
    if not AUDIT_MARKDOWN_PATH_RE.search(segment):
        return False
    common = DIRECT_MUTATOR_RE.search(segment) or INDIRECT_AUDIT_WRITE_RE.search(segment)
    powershell = tool == "PowerShell" and POWERSHELL_AUDIT_WRITE_RE.search(segment)
    return bool(common or powershell)


def _shell_direct_audit_write(command: str, tool: str) -> bool:
    if not AUDIT_MARKDOWN_PATH_RE.search(command):
        return False
    segments = _shell_segments(command)
    runtime = [seg for seg in segments if RUNTIME_SEGMENT_RE.match(seg)]
    if not runtime:
        # Whole-command matching keeps pipelines such as `cat x | sed ... | tee x` and
        # PowerShell `(Get-Content x) -replace ... | Set-Content x` detectable.
        common = DIRECT_MUTATOR_RE.search(command) or INDIRECT_AUDIT_WRITE_RE.search(command)
        powershell = tool == "PowerShell" and POWERSHELL_AUDIT_WRITE_RE.search(command)
        return bool(common or powershell)
    if any(_segment_writes_audit(seg, tool) for seg in runtime):
        return True
    rest = "\n".join(seg for seg in segments if seg not in runtime)
    if not rest or not AUDIT_MARKDOWN_PATH_RE.search(rest):
        return False
    common = DIRECT_MUTATOR_RE.search(rest) or INDIRECT_AUDIT_WRITE_RE.search(rest)
    powershell = tool == "PowerShell" and POWERSHELL_AUDIT_WRITE_RE.search(rest)
    return bool(common or powershell)


def _run_audit(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    audit = plugin_root() / "scripts" / "audit.py"
    cmd = [sys.executable, str(audit), "--root", str(project), *args]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=12, check=False)
    except subprocess.TimeoutExpired:
        # Stay below the 15-second hook timeout and report instead of crashing the hook.
        return subprocess.CompletedProcess(cmd, 124, "", f"audit {' '.join(args)} timed out after 12 seconds")


# Codex sends apply_patch source text in tool_input.command, not Edit/Write fields.
PATCH_FILE_RE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to: (.+)$")
STATUS_FIELD_RE = re.compile(r"^\s*(?:\*\*)?(?:Verification\s+)?Status(?:\*\*)?\s*:", re.IGNORECASE)


def _patch_changes(command: str) -> list[dict]:
    changes: list[dict] = []
    current = None
    for line in command.splitlines():
        match = PATCH_FILE_RE.match(line)
        if match:
            current = {"operation": match[1], "paths": [match[2]], "lines": []}
            changes.append(current)
        elif line == "*** End Patch":
            current = None
        elif current is not None:
            move = PATCH_MOVE_RE.match(line)
            if move:
                current["operation"] = "Move"
                current["paths"].append(move[1])
            elif line.startswith(("+", "-")):
                current["lines"].append(line[1:])
    return changes


def _is_audit_record(path: str, payload: dict) -> bool:
    candidate = Path(path.replace("\\", "/"))
    cwd = payload.get("cwd")
    base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else project_dir(payload)
    if not candidate.is_absolute():
        candidate = base / candidate
    parts = candidate.resolve().parts
    return (candidate.suffix.lower() == ".md" and any(
        parts[i] == "audit" and parts[i + 1] in {"tickets", "verification", "triage"}
        for i in range(len(parts) - 2)
    ))


def _patch_audit_changes(payload: dict) -> list[dict]:
    command = _tool_input(payload).get("command")
    if not isinstance(command, str):
        return []
    return [change for change in _patch_changes(command)
            if any(_is_audit_record(path, payload) for path in change["paths"])]


def _shell_command(tool_input: dict) -> str:
    # Codex hooks normally canonicalize exec_command to Bash/command.
    return str(tool_input.get("command") or tool_input.get("cmd") or "")


def pre_tool_use(payload: dict) -> int:
    tool = _tool_name(payload)
    tin = _tool_input(payload)

    if tool == "apply_patch":
        for change in _patch_audit_changes(payload):
            if change["operation"] != "Update" or any(STATUS_FIELD_RE.search(line) for line in change["lines"]):
                return _deny(
                    "Direct apply_patch creation, deletion, moves, or status edits of audit records are blocked. "
                    "Use the audit MCP/CLI runtime for supported lifecycle changes."
                )
        return 0

    if tool in {"Bash", "PowerShell", "exec_command", "shell_command"}:
        command = _shell_command(tin)
        if _shell_direct_audit_write(command, tool):
            return _deny(
                "Audit markdown lifecycle state must be changed through the audit MCP/CLI runtime, not shell rewrites. "
                "Use the structured audit lifecycle tools or the bundled scripts/audit.py CLI fallback."
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
    if _tool_name(payload) == "apply_patch":
        touched = bool(_patch_audit_changes(payload))
    else:
        touched = _touches_audit_file(tin)
    if not touched:
        return 0
    project = project_dir(payload)
    if not (project / "audit").exists():
        return 0
    result = _run_audit(project, "doctor")
    if result.returncode == 0:
        return 0
    details = (result.stderr or result.stdout or "audit doctor failed").strip()
    return _context(
        "PostToolUse",
        "Audit workflow doctor found issues after audit file changes. Prefer `audit_doctor(fix=true)` or the bundled CLI fallback.\n"
        + details[:4000],
    )


def session_start(payload: dict) -> int:
    project = project_dir(payload)
    if not (project / "audit").exists():
        return 0
    return _context(
        "SessionStart",
        "Audit Workflow state exists for this project. Prefer the structured audit MCP tools; use the bundled scripts/audit.py CLI only as fallback.",
    )


def stop(payload: dict) -> int:
    if bool(payload.get("stop_hook_active")):
        return 0
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
