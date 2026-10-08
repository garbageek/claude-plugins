#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from plugin_root import plugin_root, project_dir

AUDIT_MARKDOWN_PATH = r"(?:[^\s'\";&|<>]+[\\/])*audit[\\/](?:tickets|verification|triage)[\\/][^\s'\";&|<>]+\.md"
AUDIT_FILE_RE = re.compile(rf"(?:^|[\s'\"<>=|&;]){AUDIT_MARKDOWN_PATH}")
AUDIT_MARKDOWN_PATH_RE = re.compile(AUDIT_MARKDOWN_PATH, re.IGNORECASE)
DIRECT_MUTATOR_RE = re.compile(r"\b(?:sed|perl|python|python3|ruby|node|awk|ed)\b.*(?:Verification\s+)?Status\s*:", re.IGNORECASE | re.DOTALL)
INPLACE_MUTATOR_RE = re.compile(
    r"\b(?:sed|perl|ruby)\b[^\n;&|]*\s(?:--in-place(?:=\S*)?|-[^\s]*i[^\s]*)(?=\s|$)",
    re.IGNORECASE,
)
INDIRECT_AUDIT_WRITE_RE = re.compile(
    rf"(?:"
    rf"\b(?:mv|cp|tee|install|rsync|dd|truncate|rm)\b[^\n;&|]*{AUDIT_MARKDOWN_PATH}"
    rf"|(?:>|>>)\s*{AUDIT_MARKDOWN_PATH}"
    rf")",
    re.IGNORECASE | re.DOTALL,
)
POWERSHELL_AUDIT_WRITE_RE = re.compile(
    rf"(?:"
    rf"\b(?:Set-Content|Add-Content|Out-File|Move-Item|Copy-Item|Rename-Item|Remove-Item)\b[^\n;|]*{AUDIT_MARKDOWN_PATH}"
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


def _touches_audit_file(payload: dict) -> bool:
    tool_input = _tool_input(payload)
    paths = _file_paths(tool_input)
    if paths:
        return any(_is_audit_record(path, payload) for path in paths)
    return any(_is_audit_record(m.group(0), payload)
               for m in AUDIT_MARKDOWN_PATH_RE.finditer(_as_text(tool_input)))


def _edits_change_status(tool_input: dict, payload: dict) -> bool:
    """Simulate Claude Edit/MultiEdit substitutions on real audit records.

    Comparing the resulting status *fields*, not arbitrary text in a tool
    payload, catches value-only changes (DRAFT -> OPEN) without rejecting an
    evidence sentence such as "Evidence: HTTP Status: PASS was observed".
    """
    operations = tool_input.get("edits")
    if not isinstance(operations, list):
        operations = [tool_input]
    if not operations or not all(
        isinstance(op, dict) and isinstance(op.get("old_string"), str)
        and isinstance(op.get("new_string"), str) for op in operations
    ):
        return True  # Unknown edit format: do not silently bypass audit guards.

    paths = _file_paths(tool_input)
    if not paths:
        return True
    for path in paths:
        if not _is_audit_record(path, payload):
            continue
        candidate = Path(path.replace("\\", "/")).expanduser()
        cwd = payload.get("cwd")
        base = Path(cwd).expanduser() if isinstance(cwd, str) and cwd else project_dir(payload)
        if not candidate.is_absolute():
            candidate = base / candidate
        try:
            original = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return True  # Missing/unreadable machine state must not be rewritten.
        updated = original
        for op in operations:
            # A multi-file payload may contain independent edits; apply only
            # substitutions belonging to this record, not those for a fixture.
            op_paths = _file_paths(op)
            if op_paths and path not in op_paths:
                continue
            old, new = op["old_string"], op["new_string"]
            if not old or old not in updated:
                return True  # Unrecognized substitution; refuse on managed state.
            updated = updated.replace(old, new, -1 if op.get("replace_all") else 1)
        if _status_fields(original) != _status_fields(updated):
            return True
    return False


def _status_fields(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if STATUS_FIELD_RE.match(line)]


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
    common = (DIRECT_MUTATOR_RE.search(segment) or INPLACE_MUTATOR_RE.search(segment)
              or INDIRECT_AUDIT_WRITE_RE.search(segment))
    powershell = tool == "PowerShell" and POWERSHELL_AUDIT_WRITE_RE.search(segment)
    return bool(common or powershell)


def _shell_direct_audit_write(command: str, tool: str, payload: dict) -> bool:
    if not any(_is_audit_record(m.group(0), payload)
               for m in AUDIT_MARKDOWN_PATH_RE.finditer(command)):
        return False
    segments = _shell_segments(command)
    runtime = [seg for seg in segments if RUNTIME_SEGMENT_RE.match(seg)]
    if not runtime:
        # Whole-command matching keeps pipelines such as `cat x | sed ... | tee x` and
        # PowerShell `(Get-Content x) -replace ... | Set-Content x` detectable.
        common = (DIRECT_MUTATOR_RE.search(command) or INPLACE_MUTATOR_RE.search(command)
                  or INDIRECT_AUDIT_WRITE_RE.search(command))
        powershell = tool == "PowerShell" and POWERSHELL_AUDIT_WRITE_RE.search(command)
        return bool(common or powershell)
    if any(_segment_writes_audit(seg, tool) for seg in runtime):
        return True
    rest = "\n".join(seg for seg in segments if seg not in runtime)
    if not rest or not AUDIT_MARKDOWN_PATH_RE.search(rest):
        return False
    common = (DIRECT_MUTATOR_RE.search(rest) or INPLACE_MUTATOR_RE.search(rest)
              or INDIRECT_AUDIT_WRITE_RE.search(rest))
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
STATUS_FIELD_RE = re.compile(r"^\s*(?:\*\*(?:Verification\s+)?Status:\*\*|(?:Verification\s+)?Status\s*:)", re.IGNORECASE)


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
    project = project_dir(payload)
    cwd = payload.get("cwd")
    base = Path(cwd).expanduser().resolve() if isinstance(cwd, str) and cwd else project
    candidate = Path(path.replace("\\", "/")).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    # abspath removes .. without following symlinks: logical audit/tickets paths
    # must remain protected even when the directory points outside the project.
    logical = Path(os.path.abspath(candidate))
    if logical.suffix.lower() != ".md":
        return False
    resolved = logical.resolve()
    for kind in ("tickets", "verification", "triage"):
        audit_dir = project / "audit" / kind
        if logical.is_relative_to(audit_dir) or resolved.is_relative_to(audit_dir.resolve()):
            return True
        # Verification details are stored one level deeper and may themselves
        # be symlinked to an external evidence directory.
        if kind == "verification" and resolved.is_relative_to((audit_dir / "details").resolve()):
            return True
    return False


def _patch_audit_changes(payload: dict) -> list[dict]:
    command = _shell_command(_tool_input(payload))
    if not command:
        return []
    return [change for change in _patch_changes(command)
            if any(_is_audit_record(path, payload) for path in change["paths"])]


def _unsafe_audit_patch(payload: dict) -> bool:
    return any(change["operation"] != "Update" or any(
        STATUS_FIELD_RE.search(line) for line in change["lines"])
        for change in _patch_audit_changes(payload))


def _shell_command(tool_input: dict) -> str:
    # Codex hooks normally canonicalize exec_command to Bash/command.
    return str(tool_input.get("command") or tool_input.get("cmd") or "")


# Detect common shell-invoked apply_patch with the patch inline. This is a
# best-effort tool guard, not a general shell interpreter or filesystem sandbox.
SHELL_APPLY_PATCH_RE = re.compile(r"\bapply_patch(?=\s|$)")


def pre_tool_use(payload: dict) -> int:
    tool = _tool_name(payload)
    tin = _tool_input(payload)

    if tool == "apply_patch":
        if _unsafe_audit_patch(payload):
            return _deny(
                "Direct apply_patch creation, deletion, moves, or status edits of audit records are blocked. "
                "Use the audit MCP/CLI runtime for supported lifecycle changes."
            )
        return 0

    if tool in {"Bash", "PowerShell", "exec_command", "shell_command"}:
        command = _shell_command(tin)
        if SHELL_APPLY_PATCH_RE.search(command) and _unsafe_audit_patch(payload):
            return _deny(
                "Shell-invoked apply_patch cannot create, delete, move, or directly change "
                "lifecycle statuses in audit records. Use the audit MCP/CLI runtime."
            )
        if _shell_direct_audit_write(command, tool, payload):
            return _deny(
                "Audit markdown lifecycle state must be changed through the audit MCP/CLI runtime, not shell rewrites. "
                "Use the structured audit lifecycle tools or the bundled scripts/audit.py CLI fallback."
            )
        return 0

    if tool == "Write" and _touches_audit_file(payload):
        return _deny(
            "Full Write of machine-managed audit records is blocked, regardless of content. "
            "Use the audit CLI/MCP runtime for lifecycle changes."
        )
    if tool in {"Edit", "MultiEdit"} and _touches_audit_file(payload):
        if _edits_change_status(tin, payload):
            return _deny(
                "Direct changes to audit Status/Verification Status fields are blocked. "
                "Use audit CLI/MCP commands so role, state-machine, and evidence gates run."
            )
    return 0


def post_tool_use(payload: dict) -> int:
    tin = _tool_input(payload)
    tool = _tool_name(payload)
    if tool == "apply_patch" or (tool in {"Bash", "PowerShell", "exec_command", "shell_command"}
                                  and SHELL_APPLY_PATCH_RE.search(_shell_command(tin))):
        touched = bool(_patch_audit_changes(payload)) or _touches_audit_file(payload)
    else:
        touched = _touches_audit_file(payload)
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
