#!/usr/bin/env python3
"""Deterministic control-band detection for the maintain loop. No model is involved.

For each metric in bands.yaml: fetch its series (oldest -> newest) from the metric's source,
build a rolling baseline, apply Western Electric rules to the most recent points and map the
most severe broken rule to a response tier (none | 1sigma | 2sigma | 3sigma).

Usage:
    python3 monitoring/detect.py                          # all metrics, findings to stdout
    python3 monitoring/detect.py --out findings.json      # also write the findings file
    python3 monitoring/detect.py --metric ci_test_failure_rate
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

TIERS = ["none", "1sigma", "2sigma", "3sigma"]
DEFAULTS = {"baseline_points": 30, "min_baseline_points": 10, "eval_points": 8}


# --------------------------------------------------------------- rules ---

def western_electric(tail_z: list[float]) -> tuple[str, str | None]:
    """Most severe rule broken by the END of tail_z (z-scores, positive = bad side).

    R1: the last point beyond 3σ                       -> 3sigma
    R2: 2 of the last 3 points beyond 2σ               -> 2sigma
    R3: 4 of the last 5 points beyond 1σ               -> 1sigma
    R4: the last 8 points all on the bad side of mean  -> 1sigma (slow drift)
    """
    if not tail_z:
        return "none", None
    if tail_z[-1] > 3:
        return "3sigma", "R1"
    if len(tail_z) >= 3 and sum(z > 2 for z in tail_z[-3:]) >= 2 and tail_z[-1] > 2:
        return "2sigma", "R2"
    if len(tail_z) >= 5 and sum(z > 1 for z in tail_z[-5:]) >= 4 and tail_z[-1] > 1:
        return "1sigma", "R3"
    if len(tail_z) >= 8 and all(z > 0 for z in tail_z[-8:]):
        return "1sigma", "R4"
    return "none", None


def evaluate(series: list[float], direction: str = "up", baseline_points: int = 30,
             min_baseline_points: int = 10, eval_points: int = 8) -> dict:
    """Evaluate a series and return tier, rule and the numbers behind the decision."""
    if len(series) < min_baseline_points + 1:
        return {"tier": "none", "rule": None, "status": "insufficient_data", "points": len(series)}

    eval_points = max(1, min(eval_points, len(series) - min_baseline_points))
    tail = series[-eval_points:]
    baseline = series[:-eval_points][-baseline_points:]
    if len(baseline) < min_baseline_points:
        return {"tier": "none", "rule": None, "status": "insufficient_data", "points": len(series)}

    mean = statistics.fmean(baseline)
    std = statistics.pstdev(baseline)
    if std == 0:
        # A perfectly flat baseline: any move away from it is maximally unusual.
        z_up = [0.0 if v == mean else (10.0 if v > mean else -10.0) for v in tail]
    else:
        z_up = [(v - mean) / std for v in tail]

    candidates = []
    if direction in ("up", "both"):
        candidates.append(western_electric(z_up) + ("up",))
    if direction in ("down", "both"):
        candidates.append(western_electric([-z for z in z_up]) + ("down",))
    tier, rule, side = max(candidates, key=lambda c: TIERS.index(c[0]))

    return {
        "tier": tier,
        "rule": rule,
        "side": side if rule else None,
        "status": "ok",
        "latest": tail[-1],
        "mean": round(mean, 6),
        "std": round(std, 6),
        "z_latest": round(z_up[-1], 3),
        "points": len(series),
    }


# -------------------------------------------------------------- inputs ---

def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.exit("detect.py: PyYAML is required to read bands.yaml (pip install pyyaml)")
    return yaml.safe_load(text)


def parse_series(raw: str) -> list[float]:
    """Accepts a JSON list of numbers or of {"t": ..., "v": number} objects."""
    data = json.loads(raw or "[]")
    out = []
    for item in data:
        value = item.get("v") if isinstance(item, dict) else item
        if value is not None:
            out.append(float(value))
    return out


def fetch_series(metric: dict, root: Path) -> list[float]:
    source = metric.get("source") or {}
    if "file" in source:
        return parse_series((root / source["file"]).read_text(encoding="utf-8"))
    if "command" in source:
        proc = subprocess.run(source["command"], shell=True, cwd=root, capture_output=True,
                              text=True, timeout=int(source.get("timeout", 120)))
        if proc.returncode != 0:
            raise RuntimeError(f"source command failed ({proc.returncode}): {proc.stderr.strip()[:300]}")
        return parse_series(proc.stdout)
    raise RuntimeError("metric has no source.command or source.file")


# ---------------------------------------------------------------- main ---

def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bands", type=Path, default=root / "monitoring" / "bands.yaml")
    ap.add_argument("--metric", help="evaluate only this metric")
    ap.add_argument("--out", type=Path, help="write all findings to this JSON file")
    args = ap.parse_args(argv)

    cfg = load_config(args.bands)
    defaults = {**DEFAULTS, **(cfg.get("defaults") or {})}
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    findings = []

    for metric in cfg.get("metrics") or []:
        name = metric["name"]
        if args.metric and name != args.metric:
            continue
        try:
            series = fetch_series(metric, root)
            result = evaluate(series, metric.get("direction", "up"),
                              int(defaults["baseline_points"]), int(defaults["min_baseline_points"]),
                              int(defaults["eval_points"]))
        except Exception as exc:  # one broken source must not stop the others
            result = {"tier": "none", "rule": None, "status": f"error: {exc}"}

        tier_cfg = (metric.get("tiers") or {}).get(result["tier"], {}) if result["tier"] != "none" else {}
        finding = {
            "metric": name,
            "owner": metric.get("owner"),
            "description": metric.get("description"),
            "detected_at": now,
            **result,
            "action": tier_cfg.get("action", "none"),
            "mode": tier_cfg.get("mode", "read-only"),
            "routes": tier_cfg.get("routes", []),
        }
        findings.append(finding)
        print(f"{name}: tier={finding['tier']} rule={finding['rule']} action={finding['action']} "
              f"status={finding['status']}", file=sys.stderr)

    payload = {"generated_at": now, "runbooks": cfg.get("runbooks") or {}, "findings": findings}
    print(json.dumps(payload, indent=2))
    if args.out:
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    actionable = any(f["action"] in ("diagnose", "propose", "report") for f in findings)
    if gh_out := os.environ.get("GITHUB_OUTPUT"):
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"actionable={'true' if actionable else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
