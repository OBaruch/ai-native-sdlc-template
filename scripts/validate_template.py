#!/usr/bin/env python3
"""Validates the AI-native SDLC scaffold. Run: make validate-template

Checks
- every tracked *.json parses; every *.yml / *.yaml parses (needs PyYAML)
- every *.sh passes `bash -n` (when bash is available)
- skills: SKILL.md frontmatter has name + description, and name == folder
- agents: frontmatter has name + description; commands: frontmatter has description
- hook commands in .claude/settings.json point at files that exist
- evals: id, prompt and at least one check
- monitoring/bands.yaml: runbook routes are declared and their docs exist
- intent template keeps the required sections
Exit code 1 if anything fails.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".runs", "worktrees"}
errors: list[str] = []
warnings: list[str] = []


def files(pattern: str) -> list[Path]:
    return sorted(p for p in ROOT.rglob(pattern)
                  if not any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts))


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def frontmatter(p: Path) -> dict[str, str] | None:
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(m.group(1)) or {}
        return {str(k): str(v) for k, v in data.items()}
    except ImportError:
        return dict(re.findall(r"^([A-Za-z_-]+):\s*(.+)$", m.group(1), re.M))
    except Exception as exc:  # malformed YAML
        errors.append(f"{rel(p)}: frontmatter is not valid YAML ({exc})")
        return {}


def check_json() -> None:
    for p in files("*.json"):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel(p)}: invalid JSON ({exc})")


def check_yaml() -> None:
    try:
        import yaml  # type: ignore
    except ImportError:
        warnings.append("PyYAML not installed: YAML files not parsed (pip install pyyaml)")
        return
    for p in files("*.yml") + files("*.yaml"):
        try:
            list(yaml.safe_load_all(p.read_text(encoding="utf-8")))
        except Exception as exc:
            errors.append(f"{rel(p)}: invalid YAML ({exc})")


def check_shell() -> None:
    bash = shutil.which("bash")
    if not bash:
        warnings.append("bash not found: shell syntax not checked")
        return
    for p in files("*.sh"):
        r = subprocess.run([bash, "-n", str(p)], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"{rel(p)}: bash syntax error: {r.stderr.strip()}")
        if b"\r\n" in p.read_bytes():
            errors.append(f"{rel(p)}: CRLF line endings (bash on Linux will fail)")


def check_claude_dir() -> None:
    for p in files("SKILL.md"):
        fm = frontmatter(p)
        if not fm or not fm.get("name") or not fm.get("description"):
            errors.append(f"{rel(p)}: needs frontmatter with name and description")
        elif fm["name"] != p.parent.name:
            errors.append(f"{rel(p)}: name '{fm['name']}' must match folder '{p.parent.name}'")
    for p in (ROOT / ".claude" / "agents").glob("*.md"):
        fm = frontmatter(p)
        if not fm or not fm.get("name") or not fm.get("description"):
            errors.append(f"{rel(p)}: agent needs frontmatter with name and description")
    for p in (ROOT / ".claude" / "commands").glob("*.md"):
        fm = frontmatter(p)
        if not fm or not fm.get("description"):
            errors.append(f"{rel(p)}: command needs frontmatter with description")

    settings = ROOT / ".claude" / "settings.json"
    if settings.exists():
        data = json.loads(settings.read_text(encoding="utf-8"))
        for event, groups in (data.get("hooks") or {}).items():
            for group in groups:
                for hook in group.get("hooks", []):
                    for ref in re.findall(r"\$CLAUDE_PROJECT_DIR/([^\"' ]+)", hook.get("command", "")):
                        if not (ROOT / ref).exists():
                            errors.append(f".claude/settings.json: {event} hook points to missing {ref}")


def check_evals() -> None:
    for p in (ROOT / "evals").glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue  # reported by check_json
        for key in ("id", "prompt", "checks"):
            if not data.get(key):
                errors.append(f"{rel(p)}: eval needs '{key}'")


def check_bands() -> None:
    bands = ROOT / "monitoring" / "bands.yaml"
    try:
        import yaml  # type: ignore
    except ImportError:
        return
    if not bands.exists():
        errors.append("monitoring/bands.yaml is missing")
        return
    cfg = yaml.safe_load(bands.read_text(encoding="utf-8")) or {}
    runbooks = cfg.get("runbooks") or {}
    for name, rb in runbooks.items():
        doc = (rb or {}).get("doc")
        if doc and not (ROOT / doc).exists():
            errors.append(f"bands.yaml: runbook '{name}' doc {doc} does not exist")
        wf = (rb or {}).get("workflow")
        if wf and not (ROOT / ".github" / "workflows" / wf).exists():
            errors.append(f"bands.yaml: runbook '{name}' workflow {wf} does not exist")
    for metric in cfg.get("metrics") or []:
        for tier, tcfg in (metric.get("tiers") or {}).items():
            for route in (tcfg or {}).get("routes", []) or []:
                if str(route).startswith("runbook:") and route.split(":", 1)[1] not in runbooks:
                    errors.append(f"bands.yaml: {metric['name']} {tier} uses undeclared {route}")


def check_intent_template() -> None:
    required = {
        "intent.md": ["## Problem", "## Proposed outcome", "## Affected users and systems",
                      "## Constraints", "## Open questions"],
        "spec.md": ["## Requirements", "## Design", "## Areas of concern"],
        "plan.md": ["## Files that change", "## Order of work", "## Risks", "## Proof"],
    }
    base = ROOT / "intent" / "0000-template"
    for name, sections in required.items():
        p = base / name
        if not p.exists():
            errors.append(f"intent/0000-template/{name} is missing")
            continue
        text = p.read_text(encoding="utf-8")
        for s in sections:
            if s not in text:
                errors.append(f"intent/0000-template/{name}: missing section '{s}'")


def main() -> int:
    for check in (check_json, check_yaml, check_shell, check_claude_dir, check_evals,
                  check_bands, check_intent_template):
        check()
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    print(f"\nvalidate-template: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
