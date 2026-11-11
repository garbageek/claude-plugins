#!/usr/bin/env python3
"""CLAUDE CODE ONLY: run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries in isolated projects. Outputs results as JSON.
"""

import argparse
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def find_project_root() -> Path:
    """Return the calling project for legacy runner compatibility.

    Trigger subprocesses use their own temporary projects and never modify it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def _matches_tool_use(tool_name: str, tool_input: dict, command_name: str) -> bool:
    """Recognize only an actual invocation of the synthetic command."""
    if not isinstance(tool_input, dict):
        return False
    if tool_name == "Skill":
        value = tool_input.get("skill")
        return isinstance(value, str) and (
            value == command_name or value.endswith(f":{command_name}")
        )
    if tool_name == "Read":
        value = tool_input.get("file_path")
        return isinstance(value, str) and (
            value.replace("\\", "/").rsplit("/", 1)[-1] == f"{command_name}.md"
        )
    return False


def _is_trigger_event(
    event: dict, command_name: str, tool_blocks: dict[int, dict]
) -> bool:
    """Inspect full assistant messages and incremental stream-json tool calls."""
    if not isinstance(event, dict):
        return False
    if event.get("type") == "assistant":
        for item in (event.get("message") or {}).get("content", []):
            if item.get("type") == "tool_use" and _matches_tool_use(
                item.get("name", ""), item.get("input") or {}, command_name
            ):
                return True
        return False

    if event.get("type") != "stream_event":
        return False

    stream_event = event.get("event") or {}
    event_type = stream_event.get("type")
    index = stream_event.get("index")

    if event_type == "content_block_start":
        block = stream_event.get("content_block") or {}
        if block.get("type") == "tool_use":
            tool_blocks[index] = {"name": block.get("name", ""), "json": ""}
            return _matches_tool_use(block.get("name", ""), block.get("input") or {}, command_name)

    elif event_type == "content_block_delta" and index in tool_blocks:
        delta = stream_event.get("delta") or {}
        if delta.get("type") == "input_json_delta":
            state = tool_blocks[index]
            state["json"] += delta.get("partial_json", "")
            try:
                tool_input = json.loads(state["json"])
            except json.JSONDecodeError:
                return False
            return _matches_tool_use(state["name"], tool_input, command_name)

    elif event_type == "content_block_stop":
        state = tool_blocks.pop(index, None)
        if state:
            try:
                tool_input = json.loads(state["json"])
            except json.JSONDecodeError:
                return False
            return _matches_tool_use(state["name"], tool_input, command_name)

    return False


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Measure whether Claude invokes the command in an isolated project.

    Each invocation gets its own .claude/commands directory, so parallel
    workers cannot accidentally select one another's synthetic skills.
    """
    # Keep the argument for existing callers, but do not inherit their
    # project's commands or local skill definitions during a trigger eval.
    _ = project_root
    command_name = f"{skill_name}-skill"
    with tempfile.TemporaryDirectory(prefix="create-skill-trigger-") as workdir:
        commands_dir = Path(workdir) / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        indented_desc = "\n  ".join(skill_description.split("\n"))
        (commands_dir / f"{command_name}.md").write_text(
            f"---\ndescription: |\n  {indented_desc}\n---\n\n"
            f"# {skill_name}\n\nThis skill handles: {skill_description}\n",
            encoding="utf-8",
        )

        cmd = [
            "claude", "-p", query,
            "--output-format", "stream-json",
            "--verbose", "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])
        env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=workdir, env=env, text=True, encoding="utf-8", errors="replace",
        )

        lines: queue.Queue[str | None] = queue.Queue()

        def collect_stdout() -> None:
            try:
                for line in process.stdout:
                    lines.put(line)
            finally:
                lines.put(None)

        reader = threading.Thread(target=collect_stdout, daemon=True)
        reader.start()
        tool_blocks: dict[int, dict] = {}
        deadline = time.monotonic() + timeout
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"claude -p exceeded {timeout}s")
                try:
                    line = lines.get(timeout=remaining)
                except queue.Empty:
                    raise TimeoutError(f"claude -p exceeded {timeout}s") from None
                if line is None:
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if _is_trigger_event(event, command_name, tool_blocks):
                    return True

            try:
                returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(f"claude -p exceeded {timeout}s") from exc
            if returncode != 0:
                raise RuntimeError(f"claude -p exited with status {returncode}")
            return False
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()
            reader.join(timeout=1)


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run all eval cases, preserving order and distinguishing failures."""
    if num_workers < 1 or runs_per_query < 1 or timeout < 1:
        raise ValueError("workers, runs per query, and timeout must be positive")
    if not 0 < trigger_threshold <= 1:
        raise ValueError("trigger threshold must be in (0, 1]")
    if not eval_set:
        raise ValueError("eval set must contain at least one query")
    for index, item in enumerate(eval_set):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("query"), str)
            or not item["query"].strip()
            or not isinstance(item.get("should_trigger"), bool)
        ):
            raise ValueError(f"invalid eval case at index {index}: expected query and should_trigger")

    observations: list[list[bool]] = [[] for _ in eval_set]
    errors = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        jobs = {
            executor.submit(
                run_single_query, item["query"], skill_name, description,
                timeout, str(project_root), model,
            ): index
            for index, item in enumerate(eval_set)
            for _ in range(runs_per_query)
        }
        for job in as_completed(jobs):
            index = jobs[job]
            try:
                observations[index].append(job.result())
            except Exception as exc:
                errors.append(f"{eval_set[index]['query'][:80]!r}: {exc}")
    if errors:
        raise RuntimeError(
            "Trigger evaluation failed; no scores were produced:\n"
            + "\n".join(errors)
        )

    results = []
    for item, outcomes in zip(eval_set, observations):
        rate = sum(outcomes) / len(outcomes)
        expected = item["should_trigger"]
        results.append({
            "query": item["query"],
            "should_trigger": expected,
            "trigger_rate": rate,
            "triggers": sum(outcomes),
            "runs": len(outcomes),
            "pass": rate >= trigger_threshold if expected else rate < trigger_threshold,
        })

    passed = sum(item["pass"] for item in results)
    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
    }

def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
