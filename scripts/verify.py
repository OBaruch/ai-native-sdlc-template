#!/usr/bin/env python3
"""Run verification and bind its success to the exact working tree contents."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def fingerprint(root: Path) -> str:
    files = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root).split(b"\0")
    digest = hashlib.sha256(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root))
    for name in sorted(set(files) - {b""}):
        path = root / name.decode("utf-8")
        digest.update(name + b"\0")
        if path.is_symlink():
            digest.update(str(path.readlink()).encode())
        elif path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<deleted>")
    return digest.hexdigest()


def check(root: Path) -> bool:
    status = subprocess.run(["git", "status", "--porcelain", "-z"], cwd=root, capture_output=True)
    if status.returncode or not status.stdout:
        return True
    tracked = subprocess.check_output(["git", "diff", "--name-only", "-z", "HEAD"], cwd=root)
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=root)
    paths = [p.decode("utf-8") for p in (tracked + untracked).split(b"\0") if p]
    # Ordinary intent/report prose does not require application checks. Canonical
    # instruction/policy changes still require scaffold verification and drift checks.
    if paths and all(p.startswith(("intent/", "docs/", "doc/", "postmortems/", "monitoring/reports/")) for p in paths):
        return True
    receipt = root / ".agents/verification.json"
    try:
        data = json.loads(receipt.read_text(encoding="utf-8"))
        return data.get("passed") is True and data.get("fingerprint") == fingerprint(root)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--template", action="store_true", help="verify the scaffold rather than an adopted application")
    args = parser.parse_args()
    root = Path.cwd()
    if args.check:
        return 0 if check(root) else 2
    before = fingerprint(root)
    command = ["make", "template-check" if args.template else "check"]
    result = subprocess.run(command)
    passed = result.returncode == 0 and before == fingerprint(root)
    receipt = root / ".agents/verification.json"
    receipt.parent.mkdir(exist_ok=True)
    receipt.write_text(json.dumps({"passed": passed, "fingerprint": before, "command": command}) + "\n", encoding="utf-8")
    return 0 if passed else result.returncode or 1


if __name__ == "__main__":
    sys.exit(main())
