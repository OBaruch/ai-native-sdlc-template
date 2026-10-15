#!/usr/bin/env python3
"""Run a selected harness through the versioned SDLC request/result contract."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

VERSION = 1
MODES = ("read-only", "workspace-write")


def argv(value: object) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise ValueError("command must be a nonempty JSON array of argument strings")
    return value


def run_process(command: list[str], request: str, workspace: Path, timeout: int) -> subprocess.CompletedProcess:
    # A timeout must stop the harness and its child tools, not just the parent CLI.
    with subprocess.Popen(command, cwd=workspace, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(request, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise TimeoutError(f"agent exceeded timeout of {timeout}s") from None
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def validate_result(result: object) -> dict:
    if not isinstance(result, dict) or type(result.get("schema_version")) is not int or result["schema_version"] != VERSION:
        raise ValueError("adapter result must have schema_version: 1")
    if result.get("status") not in ("success", "error") or not isinstance(result.get("output"), str):
        raise ValueError("adapter result requires status (success/error) and string output")
    if type(result.get("is_error")) is not bool or result["is_error"] != (result["status"] == "error"):
        raise ValueError("adapter result status and boolean is_error must agree")
    if result["status"] == "success" and not result["output"].strip():
        raise ValueError("successful adapter result must contain output")
    return result


def execute(adapter: str, prompt: str, workspace: Path, mode: str, timeout: int) -> dict:
    instructions = workspace / "AGENTS.md"
    if not instructions.is_file():
        raise ValueError(f"missing canonical instructions: {instructions}")
    prompt = instructions.read_text(encoding="utf-8") + "\n\nTask:\n" + prompt
    request = {"schema_version": VERSION, "prompt": prompt, "workspace": str(workspace),
               "mode": mode, "timeout_seconds": timeout,
               "instructions": {"entrypoint": "AGENTS.md", "skills": ".agents/skills",
                                "commands": ".agents/commands", "roles": ".agents/roles"}}
    if adapter == "command":
        command = argv(json.loads(os.environ.get("SDLC_AGENT_COMMAND", "[]")))
        supported = os.environ.get("SDLC_AGENT_MODES", "").split(",")
        if mode not in supported:
            raise ValueError(f"command adapter has not declared support for {mode}; set SDLC_AGENT_MODES")
        process = run_process(command, json.dumps(request), workspace, timeout)
        if process.returncode:
            raise RuntimeError(f"command adapter exited {process.returncode}; see adapter stderr")
        result = validate_result(json.loads(process.stdout))
    elif adapter == "claude":
        tools = "Read,Grep,Glob"
        allowed = tools
        if mode == "workspace-write":
            tools += ",Edit,Write,Bash"
            allowed += ",Edit,Write,Bash(make build),Bash(make test),Bash(make lint),Bash(make check),Bash(make template-check),Bash(git status),Bash(git diff:*)"
        process = run_process(["claude", "-p", "--output-format", "json", "--strict-mcp-config",
                               "--mcp-config", '{"mcpServers":{}}', "--tools", tools,
                               "--allowedTools", allowed], prompt, workspace, timeout)
        if process.returncode:
            raise RuntimeError(f"Claude exited {process.returncode}; see adapter stderr")
        native = json.loads(process.stdout)
        if not isinstance(native, dict) or type(native.get("is_error")) is not bool or not isinstance(native.get("result"), str):
            raise ValueError("invalid Claude result (requires is_error and result)")
        result = {"schema_version": VERSION, "status": "error" if native["is_error"] else "success",
                  "is_error": native["is_error"], "output": native["result"]}
    elif adapter == "codex":
        with tempfile.TemporaryDirectory(prefix="sdlc-codex-") as temp:
            message = Path(temp) / "message.txt"
            process = run_process(["codex", "exec", "-c", "mcp_servers={}", "--sandbox", mode, "--color", "never",
                                   "--output-last-message", str(message), "-"], prompt, workspace, timeout)
            if process.returncode:
                raise RuntimeError(f"Codex exited {process.returncode}; see adapter stderr")
            if not message.is_file() or not message.read_text(encoding="utf-8").strip():
                raise ValueError("Codex did not produce a final message")
            result = {"schema_version": VERSION, "status": "success", "is_error": False,
                      "output": message.read_text(encoding="utf-8")}
    else:
        raise ValueError(f"unknown adapter: {adapter}")
    # Never copy native transcripts, prompts, environment variables or tokens into results.
    validate_result(result)
    return {"schema_version": VERSION, "adapter": adapter, "status": result["status"],
            "is_error": result["is_error"], "output": result["output"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=("claude", "codex", "command"), default=os.environ.get("SDLC_AGENT_ADAPTER"))
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--mode", choices=MODES, default="read-only")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--text", action="store_true", help="also print normalized output text")
    args = parser.parse_args()
    result = {"schema_version": VERSION, "adapter": args.adapter, "status": "error", "is_error": True, "output": ""}
    try:
        if not args.adapter:
            raise ValueError("select an adapter with --adapter or SDLC_AGENT_ADAPTER; no default provider")
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        result = execute(args.adapter, args.prompt_file.read_text(encoding="utf-8"),
                         args.workspace.resolve(strict=True), args.mode, args.timeout)
    except (ValueError, OSError, RuntimeError, TimeoutError) as error:
        result["output"] = str(error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.text:
        print(result["output"])
    if result["is_error"]:
        print(f"agent-run: {result['output']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
