#!/usr/bin/env python3
"""Run existing skill eval cases on Claude Code or Codex and save reviewable outputs.

This measures task outcomes, NOT automatic skill triggering. No grading is invented.
External CLIs are invoked only when the user explicitly runs this helper.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from scripts.utils import parse_skill_md


SKILL_SUBDIR = {
    "claude": Path(".claude/skills"),
    "codex": Path(".agents/skills"),
}


def case_prompt(case_dir: Path) -> str:
    value = (case_dir / "prompt.md").read_text(encoding="utf-8")
    # The optional frontmatter controls Claude's native plugin eval, but should
    # not become part of the user's prompt in this cross-host evaluator.
    match = re.match(r"\A---\s*\n.*?\n---\s*\n", value, re.S)
    return value[match.end():].strip() if match else value.strip()


def parse_cases(skill_path: Path) -> list[tuple[str, str, Path]]:
    cases_dir = skill_path / "evals"
    if not cases_dir.is_dir():
        raise ValueError(f"No evals/ directory in {skill_path}")
    result = []
    for path in sorted(cases_dir.iterdir()):
        if not path.is_dir() or not (path / "prompt.md").is_file():
            continue
        prompt = case_prompt(path)
        if not prompt:
            raise ValueError(f"Case prompt is empty: {path}")
        result.append((path.name, prompt, path))
    if not result:
        raise ValueError(f"No evals/<case>/prompt.md files in {cases_dir}")
    return result


def read_agent_output(host: str, raw: str, response_file: Path) -> tuple[str, int | None]:
    if host == "codex":
        response = response_file.read_text(encoding="utf-8") if response_file.exists() else ""
        tokens = None
        for line in raw.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "turn.completed":
                usage = event.get("usage") or {}
                if isinstance(usage.get("input_tokens"), int) and isinstance(usage.get("output_tokens"), int):
                    tokens = usage["input_tokens"] + usage["output_tokens"]
        return response, tokens
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw, None
    if not isinstance(data, dict):
        return raw, None
    usage = data.get("usage") or {}
    tokens = None
    if isinstance(usage.get("input_tokens"), int) and isinstance(usage.get("output_tokens"), int):
        tokens = usage["input_tokens"] + usage["output_tokens"]
    return str(data.get("result", "")), tokens


def run_cli(host: str, prompt: str, cwd: Path, timeout: int, model: str | None) -> tuple[int, str, str, int | None, float]:
    response_file = cwd / ".agent-final-response.txt"
    if host == "codex":
        cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write", "--json", "--output-last-message", str(response_file)]
        if model:
            cmd.extend(["--model", model])
        cmd.append("-")
    else:
        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        if model:
            cmd.extend(["--model", model])
    env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
    start = time.monotonic()
    try:
        done = subprocess.run(
            cmd, cwd=cwd, env=env, input=prompt if host == "codex" else None,
            text=True, capture_output=True, timeout=timeout, check=False,
        )
        response, tokens = read_agent_output(host, done.stdout, response_file)
        return done.returncode, response, done.stderr, tokens, time.monotonic() - start
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"agent timed out after {timeout}s: {exc}", None, time.monotonic() - start


def copy_inputs(case_dir: Path, dst: Path) -> None:
    source = case_dir / "files"
    if not source.is_dir():
        return
    # shutil.copytree(..., dirs_exist_ok=True) is available on Python >= 3.8.
    shutil.copytree(source, dst, dirs_exist_ok=True)


def copy_skill(skill_path: Path, dst: Path, host: str, name: str) -> None:
    target = dst / SKILL_SUBDIR[host] / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_path, target, ignore=shutil.ignore_patterns("evals", "__pycache__", ".git", ".DS_Store", "*.pyc"))


def save_outputs(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    # Do not copy host setup, caches, or transcripts containing credentials;
    # outputs are files the agent created in the isolated project directory.
    for path in src.rglob("*"):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(src).parts):
            continue
        if path.stat().st_size > 20_000_000:
            continue
        relative = path.relative_to(src)
        output_file = dst / "artifacts" / relative
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, output_file)


def evaluate(args: argparse.Namespace) -> int:
    skill_path = args.skill_path.resolve()
    if not (skill_path / "SKILL.md").is_file():
        raise ValueError(f"Not an Agent Skill: {skill_path}")
    name, _, _ = parse_skill_md(skill_path)
    if name != skill_path.name:
        raise ValueError(f"Skill name mismatch: directory '{skill_path.name}' vs frontmatter '{name}'")
    cases = parse_cases(skill_path)
    configurations = ["with_skill", "without_skill"] if args.baseline else ["with_skill"]
    if args.dry_run:
        print(json.dumps({"host": args.host, "skill": name, "cases": [c[0] for c in cases],
                          "configurations": configurations, "workspace": str(args.workspace / "iteration-1")}, indent=2))
        return 0
    if shutil.which(args.host) is None:
        raise RuntimeError(f"{args.host} executable is unavailable; no model calls were made")
    workspace = args.workspace.resolve() / "iteration-1"
    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError(f"Existing results would be overwritten: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    failed = 0
    for case_name, prompt, case_dir in cases:
        case_result = workspace / case_name
        case_result.mkdir()
        (case_result / "eval_metadata.json").write_text(
            json.dumps({"eval_name": case_name, "prompt": prompt, "assertions": []}, indent=2) + "\n", encoding="utf-8")
        for configuration in configurations:
            result_dir = case_result / configuration
            result_dir.mkdir()
            with tempfile.TemporaryDirectory(prefix=f"skill-eval-{case_name}-") as tmp:
                execution_dir = Path(tmp)
                copy_inputs(case_dir, execution_dir)
                if configuration == "with_skill":
                    copy_skill(skill_path, execution_dir, args.host, name)
                code, answer, error, tokens, duration = run_cli(args.host, prompt, execution_dir, args.timeout, args.model)
                outputs = result_dir / "outputs"
                save_outputs(execution_dir, outputs)
                (outputs / "response.md").write_text(answer or "(No final response)", encoding="utf-8")
                (result_dir / "execution.json").write_text(json.dumps({
                    "host": args.host, "exit_code": code, "error": error,
                    "skill_available": configuration == "with_skill",
                    "automatic_trigger_measured": False,
                }, indent=2) + "\n", encoding="utf-8")
                timing = {"total_duration_seconds": round(duration, 3)}
                if tokens is not None:
                    timing["total_tokens"] = tokens
                (result_dir / "timing.json").write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
                if code:
                    failed += 1
                print(f"{case_name}/{configuration}: exit={code}, duration={duration:.1f}s")
    print(f"Completed {len(cases) * len(configurations)} runs; {failed} failed. Results: {workspace}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex"), required=True)
    parser.add_argument("--skill-path", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--baseline", action="store_true", help="Also run each case without the skill")
    parser.add_argument("--dry-run", action="store_true", help="Inspect cases without calling models")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        return evaluate(args)
    except (ValueError, FileExistsError, RuntimeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
