#!/usr/bin/env python3
"""Read-only prerequisite diagnosis. Never print credential values."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys


def main() -> int:
    missing = []
    for tool in ("bash", "git", "make", "shellcheck"):
        found = shutil.which(tool)
        print(f"{tool}: {'available' if found else 'MISSING'}")
        if not found:
            missing.append(tool)
    yaml = importlib.util.find_spec("yaml") is not None
    print(f"PyYAML: {'available' if yaml else 'MISSING (python3 -m pip install PyYAML==6.0.3)'}")
    if not yaml:
        missing.append("PyYAML")
    instructions = Path("AGENTS.md").is_file()
    print(f"AGENTS.md: {'available' if instructions else 'MISSING; run from the repository root'}")
    if not instructions:
        missing.append("AGENTS.md")
    adapter = os.environ.get("SDLC_AGENT_ADAPTER", "")
    if not adapter:
        print("Agent: not selected (scaffold development needs no model or credentials).")
    elif adapter in ("claude", "codex"):
        found = shutil.which(adapter)
        print(f"Agent: {adapter}; CLI {'available' if found else 'MISSING'}")
        if not found:
            missing.append(adapter)
        binding = "ANTHROPIC_API_KEY" if adapter == "claude" else "OPENAI_API_KEY"
        print(f"{binding}: {'set' if os.environ.get(binding) else 'unset; existing CLI authentication may apply'}")
        print("Credentials have not been exercised; run a representative agent task after setup.")
    elif adapter == "command":
        try:
            command = json.loads(os.environ.get("SDLC_AGENT_COMMAND", "[]"))
            if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
                raise ValueError("invalid command")
            if not shutil.which(command[0]):
                raise ValueError("adapter executable missing")
            modes = os.environ.get("SDLC_AGENT_MODES", "").split(",")
            if not modes or not all(m in ("read-only", "workspace-write") for m in modes):
                raise ValueError("declare SDLC_AGENT_MODES")
            print("Command adapter: executable available; capabilities declared, external enforcement still required.")
        except (ValueError, OSError):
            missing.append("command adapter configuration")
            print("Command adapter: invalid SDLC_AGENT_COMMAND or SDLC_AGENT_MODES.")
    else:
        missing.append("unknown adapter")
        print("Agent: unknown adapter; use claude, codex, or command.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
