#!/usr/bin/env python3
"""Evaluate any adapter in disposable clones, with independent result grading."""
from __future__ import annotations
import argparse
import glob
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid
from agent_run import run_process

ROOT = Path(__file__).resolve().parent.parent
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def grade(spec: dict, result: dict, workspace: Path) -> bool:
    outcomes = []
    for check in spec["checks"]:
        if "run" in check:
            try:
                passed = run_process(["bash", "-c", check["run"]], "", workspace, 120).returncode == 0
            except TimeoutError:
                passed = False
        else:
            passed = check["result_field"] in result and result[check["result_field"]] == check["equals"]
        print(f"  {'PASS' if passed else 'FAIL'} {check.get('name', 'unnamed')}")
        outcomes.append(passed)
    return bool(outcomes) and all(outcomes)


def load_cases(pattern: str) -> tuple[list[dict], int]:
    cases = []
    skipped = 0
    ids = set()
    for filename in sorted(glob.glob(pattern)):
        spec = json.loads(Path(filename).read_text(encoding="utf-8"))
        if not isinstance(spec, dict) or type(spec.get("enabled", True)) is not bool:
            raise ValueError(f"{filename}: enabled must be boolean")
        if not spec.get("enabled", True):
            skipped += 1
            print(f"skip {filename} (disabled)")
            continue
        case_id = spec.get("id", "")
        if not isinstance(case_id, str) or not SAFE_ID.fullmatch(case_id) or case_id in ids:
            raise ValueError(f"{filename}: invalid or duplicate id")
        if not isinstance(spec.get("prompt"), str) or not spec["prompt"].strip():
            raise ValueError(f"{filename}: prompt is required")
        checks = spec.get("checks")
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"{filename}: checks must be nonempty")
        for check in checks:
            if not isinstance(check, dict) or ("run" in check) == ("result_field" in check):
                raise ValueError(f"{filename}: each check needs run OR result_field")
            if "run" in check and (not isinstance(check["run"], str) or not check["run"].strip()):
                raise ValueError(f"{filename}: invalid check command")
            if "result_field" in check and (not isinstance(check["result_field"], str) or "equals" not in check):
                raise ValueError(f"{filename}: invalid field check")
        if spec.get("mode", "workspace-write") not in ("read-only", "workspace-write"):
            raise ValueError(f"{filename}: invalid mode")
        timeout = spec.get("timeout_seconds", 600)
        if type(timeout) is not int or timeout <= 0:
            raise ValueError(f"{filename}: invalid timeout_seconds")
        if not isinstance(spec.get("base_ref", "HEAD"), str) or not spec.get("base_ref", "HEAD"):
            raise ValueError(f"{filename}: invalid base_ref")
        ids.add(case_id)
        cases.append(spec)
    return cases, skipped


def run_cases(root: Path, cases: list[dict], adapters: list[str], output: Path) -> list[dict]:
    rows = []
    output.mkdir(parents=True)
    for spec in cases:
        ref = spec.get("base_ref", "HEAD")
        commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", ref + "^{commit}"], cwd=root, text=True).strip()
        for adapter in adapters:
            case_id = spec["id"]
            print(f"run {case_id} ({adapter})", flush=True)
            result_path = output / f"{case_id}.{adapter}.json"
            prompt_path = output / f"{case_id}.prompt.md"
            prompt_path.write_text(spec["prompt"], encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="sdlc-eval-") as temp:
                workspace = Path(temp) / "repo"
                subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", "--", str(root), str(workspace)], check=True)
                subprocess.run(["git", "checkout", "--quiet", "--detach", commit], cwd=workspace, check=True)
                process = subprocess.run([sys.executable, str(ROOT / "scripts/agent_run.py"), "--adapter", adapter,
                    "--workspace", str(workspace), "--prompt-file", str(prompt_path), "--output", str(result_path),
                    "--mode", spec.get("mode", "workspace-write"), "--timeout", str(spec.get("timeout_seconds", 600))])
                result = json.loads(result_path.read_text(encoding="utf-8"))
                # Process failure can never be rescued by permissive field checks.
                passed = grade(spec, result, workspace) and process.returncode == 0 and result.get("is_error") is False
                rows.append({"id": case_id, "adapter": adapter, "commit": commit, "passed": passed})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", action="append", choices=("claude", "codex", "command"))
    parser.add_argument("--require-enabled", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    threshold = float(os.environ.get("EVAL_PASS_THRESHOLD", "0.9"))
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("EVAL_PASS_THRESHOLD must be between 0 and 1")
    cases, skipped = load_cases(os.environ.get("EVAL_FILTER", "evals/*.json"))
    adapters = list(dict.fromkeys(args.adapter or [os.environ.get("SDLC_AGENT_ADAPTER", "")]))
    if cases and (not all(a in ("claude", "codex", "command") for a in adapters)):
        raise ValueError("select an adapter before running enabled evals")
    output = root / "evals/.runs" / uuid.uuid4().hex
    rows = run_cases(root, cases, adapters, output)
    passed = sum(row["passed"] for row in rows)
    total = len(rows)
    report = {"status": "completed" if total else "skipped", "passed": passed, "total": total,
              "disabled": skipped, "threshold": threshold, "results": rows}
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = "| Eval | Adapter | Result |\n|---|---|---|\n"
    summary += "".join(f"| {r['id']} | {r['adapter']} | {'pass' if r['passed'] else 'FAIL'} |\n" for r in rows)
    summary += f"\n{passed}/{total} passed; {skipped} disabled. Threshold: {threshold}.\n"
    if not total:
        summary += "No enabled evals: SKIPPED, not a validated agent configuration.\n"
    (root / "evals/.runs/summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(summary)
    return (0 if not args.require_enabled else 2) if not total else (0 if passed / total >= threshold else 1)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"evals: {error}", file=sys.stderr)
        sys.exit(2)
