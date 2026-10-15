#!/usr/bin/env python3
"""Evaluate canonical tool events. A missing/invalid decision always denies."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HOOKS = {"before": {"shell": ["production-gate", "protect-tests", "plan-sync"],
                    "write": ["protected-paths", "protect-tests", "block-secrets"],
                    "read": ["block-secrets"]},
         "after": {"write": ["format-lint"], "shell": [], "read": []},
         "finish": {"none": ["require-verification"]}}
ROOT = Path(__file__).resolve().parent.parent


def evaluate(event: object, project: Path, hook: str | None = None) -> dict:
    if not isinstance(event, dict) or type(event.get("schema_version")) is not int or event["schema_version"] != 1:
        raise ValueError("event requires schema_version: 1")
    phase = event.get("phase")
    operation = event.get("operation")
    if set(event) - {"schema_version", "phase", "operation"}:
        raise ValueError("unsupported event fields")
    if not isinstance(phase, str) or not isinstance(operation, dict) or not isinstance(operation.get("kind"), str) or phase not in HOOKS or operation["kind"] not in HOOKS[phase]:
        raise ValueError("unsupported phase/operation kind")
    if set(operation) - {"kind", "command", "path", "content", "new_string", "edits", "new_source"}:
        raise ValueError("unsupported operation fields")
    kind = operation["kind"]
    required = "command" if kind == "shell" else "path"
    if kind != "none" and (not isinstance(operation.get(required), str) or not operation[required]):
        raise ValueError(f"{kind} operation requires nonempty {required}")
    if kind in ("write", "read"):
        path = Path(operation["path"].replace("\\", "/"))
        if not path.is_absolute():
            path = project / path
        try:
            operation["path"] = path.resolve().relative_to(project).as_posix()
        except ValueError:
            raise ValueError("operation path escapes the project") from None
    for field in ("content", "new_string", "edits", "new_source"):
        if field in operation and not isinstance(operation[field], (str, list) if field == "edits" else str):
            raise ValueError(f"invalid {field}")
    names = HOOKS[phase][kind]
    if hook:
        if hook not in {h for kinds in HOOKS.values() for hs in kinds.values() for h in hs}:
            raise ValueError("unknown hook")
        if hook not in names:
            raise ValueError("hook does not apply to this phase/operation")
        names = [hook]
    env = {**os.environ, "SDLC_PROJECT_DIR": str(project)}
    for name in names:
        process = subprocess.run(["bash", str(ROOT / ".agents/hooks" / f"{name}.sh")],
                                 input=json.dumps(event), capture_output=True, text=True, env=env, cwd=project, timeout=30)
        if process.returncode not in (0, 2):
            return {"decision": "deny", "reason": f"policy hook {name} failed ({process.returncode})"}
        if process.stdout.strip():
            decision = json.loads(process.stdout)
            if not isinstance(decision, dict) or decision.get("decision") not in ("allow", "deny", "ask") or not isinstance(decision.get("reason"), str):
                raise ValueError(f"invalid decision from {name}")
            if decision["decision"] != "allow":
                return decision
        if process.returncode:
            return {"decision": "deny", "reason": process.stderr.strip() or f"{name} blocked the action"}
    return {"decision": "allow", "reason": "applicable checks passed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--hook", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        result = evaluate(json.load(sys.stdin), args.project.resolve(strict=True), args.hook)
    except (ValueError, TypeError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        result = {"decision": "deny", "reason": str(error)}
    print(json.dumps(result))
    return 0 if result["decision"] == "allow" else 2


if __name__ == "__main__":
    sys.exit(main())
