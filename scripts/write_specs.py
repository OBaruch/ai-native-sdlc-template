#!/usr/bin/env python3
"""Generate accepted-intent specs through any adapter; publication stays outside the agent."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import yaml
from verify import fingerprint

ROOT = Path.cwd()


def main() -> int:
    change = os.environ.get("CHANGE", "")
    if change:
        directories = [change]
    else:
        paths = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "intent/*/intent.md"], text=True).splitlines()
        directories = sorted({str(Path(p).parent) for p in paths})
    base = os.environ.get("DEFAULT_BRANCH", "main")
    for directory in directories:
        if directory == "intent/0000-template":
            continue
        if not re.fullmatch(r"intent/[0-9]{4}-[a-z0-9-]+", directory):
            raise ValueError("invalid intent directory")
        if not (ROOT / directory / "intent.md").is_file():
            raise ValueError("intent is missing")
        if (ROOT / directory / "spec.md").exists():
            continue
        slug = Path(directory).name
        branch = f"spec/{slug}"
        with tempfile.TemporaryDirectory(prefix="sdlc-spec-") as temp:
            temp_root = Path(temp)
            workspace = temp_root / "repo"
            subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--", str(ROOT), str(workspace)], check=True)
            subprocess.run(["git", "switch", "-c", branch], cwd=workspace, check=True)
            intent = workspace / directory / "intent.md"
            intent.write_text(re.sub(r"(?m)^status: *draft\b", "status: accepted", intent.read_text()), encoding="utf-8")
            prompt = temp_root / "prompt.md"
            prompt.write_text(f"Follow .agents/commands/write-spec.md for {directory}. "
                              "The intent was accepted by merging its PR. Apply relevant .agents/skills. "
                              "Output only spec.md Markdown, including YAML frontmatter; do not write files. "
                              "Keep status: draft; humans approve the spec.", encoding="utf-8")
            output = temp_root / "result.json"
            before = fingerprint(workspace)
            child_env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
            subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "agent_run.py"), "--workspace", str(workspace),
                            "--prompt-file", str(prompt), "--mode", "read-only", "--output", str(output)],
                           env=child_env, check=True)
            if fingerprint(workspace) != before:
                raise ValueError("read-only spec adapter modified the checkout; refusing publication")
            text = json.loads(output.read_text())["output"]
            if not text.startswith("---\n"):
                raise ValueError("spec must contain YAML frontmatter")
            sections = text.split("\n---\n", 1)
            if len(sections) != 2:
                raise ValueError("spec frontmatter is incomplete")
            frontmatter = yaml.safe_load(sections[0][4:])
            if not isinstance(frontmatter, dict) or frontmatter.get("status") != "draft":
                raise ValueError("generated spec must remain draft")
            if not all(h in sections[1] for h in ("## Requirements", "## Design", "## Areas of concern")):
                raise ValueError("spec is missing required sections")
            (workspace / directory / "spec.md").write_text(text + "\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", directory], cwd=workspace, check=True)
            subprocess.run(["git", "-c", "user.name=intent-to-spec[bot]", "-c", "user.email=intent-to-spec@users.noreply.github.com",
                            "commit", "-m", f"spec: {slug}"], cwd=workspace, check=True)
            # Publish to the original remote, not the temporary clone's local origin.
            remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True).strip()
            subprocess.run(["git", "push", remote, f"HEAD:refs/heads/{branch}"], cwd=workspace, check=True)
            body = temp_root / "pr.md"
            body.write_text(f"Generated from `{directory}/intent.md` using the selected SDLC adapter.\n\n"
                            "Product owner: review the intent and resolve every Area of concern with its policy owner before approval.\n", encoding="utf-8")
            subprocess.run(["gh", "pr", "create", "--base", base, "--head", branch, "--title", f"spec: {slug}",
                            "--body-file", str(body)], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"write-specs: {error}", file=sys.stderr)
        sys.exit(1)
