#!/usr/bin/env python3
"""Install an explicitly selected, versioned native adapter CLI."""
import os
import subprocess
import sys
import re


def main() -> int:
    adapter = os.environ.get("SDLC_AGENT_ADAPTER", "")
    if adapter == "command":
        print("Command adapter: provide an installed executable via SDLC_AGENT_COMMAND.")
        return 0
    packages = {"claude": "@anthropic-ai/claude-code", "codex": "@openai/codex"}
    version = os.environ.get("SDLC_AGENT_VERSION", "")
    if adapter not in packages or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", version):
        print("Set SDLC_AGENT_ADAPTER to claude/codex and SDLC_AGENT_VERSION to an exact version.", file=sys.stderr)
        return 2
    return subprocess.run(["npm", "install", "-g", f"{packages[adapter]}@{version}"]).returncode


if __name__ == "__main__":
    sys.exit(main())
