#!/usr/bin/env python3
"""Bridge any reviewed CLI accepting a text prompt on stdin and returning text on stdout."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> int:
    result = {"schema_version": 1, "status": "error", "is_error": True, "output": ""}
    try:
        request = json.load(sys.stdin)
        if type(request.get("schema_version")) is not int or request["schema_version"] != 1:
            raise ValueError("unsupported request version")
        if Path(request["workspace"]).resolve() != Path.cwd().resolve():
            raise ValueError("request workspace differs from execution directory")
        commands = json.loads(os.environ.get("SDLC_HARNESS_MODE_COMMANDS", "{}"))
        command = commands.get(request["mode"])
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise ValueError("no reviewed CLI command configured for the requested mode")
        # No shell interpolation or invented vendor flags. The outer runner owns the timeout.
        process = subprocess.run(command, input=request["prompt"], capture_output=True, text=True)
        if process.returncode:
            raise ValueError(f"configured CLI exited {process.returncode}")
        if not process.stdout.strip():
            raise ValueError("configured CLI returned empty output")
        result.update(status="success", is_error=False, output=process.stdout)
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        result["output"] = str(error)
    print(json.dumps(result))
    return 1 if result["is_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
