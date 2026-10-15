#!/usr/bin/env python3
"""Translate Claude Code events/decisions at the adapter boundary."""
import json
import os
from pathlib import Path
import sys
from policy import evaluate


def main() -> int:
    try:
        hook = sys.argv[1]
        native = json.load(sys.stdin)
        if not isinstance(native, dict):
            raise ValueError("hook input must be an object")
        if hook == "require-verification" and native.get("stop_hook_active") is True:
            return 0  # Claude's documented recursion guard; CI remains authoritative.
        data = native.get("tool_input", {})
        if not isinstance(data, dict):
            raise ValueError("tool_input must be an object")
        phase = "finish" if hook == "require-verification" else "after" if hook == "format-lint" else "before"
        kind = "none" if phase == "finish" else "shell" if native.get("tool_name") == "Bash" or "command" in data else "write"
        operation = {"kind": kind}
        if kind == "shell":
            operation["command"] = data.get("command", "")
        elif kind == "write":
            operation["path"] = data.get("file_path") or data.get("notebook_path") or "<unspecified>"
            for field in ("content", "new_string", "edits", "new_source"):
                if field in data:
                    operation[field] = data[field]
        project = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve(strict=True)
        result = evaluate({"schema_version": 1, "phase": phase, "operation": operation}, project, hook)
        if result["decision"] == "allow":
            return 0
        if phase == "finish":
            print(json.dumps({"decision": "block", "reason": result["reason"]}))
            return 0
        if result["decision"] == "ask":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                              "permissionDecision": "ask", "permissionDecisionReason": result["reason"]}}, separators=(",", ":")))
            return 0
        print(result["reason"], file=sys.stderr)
    except (ValueError, OSError, IndexError) as error:
        print(f"BLOCKED: invalid Claude hook input ({error})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
