#!/usr/bin/env python3
"""Range query against a Prometheus-compatible API, printed as a series for detect.py.

Prints a JSON list of {"t": unix_ts, "v": value} for the first returned series.
Env: PROMETHEUS_URL (e.g. https://prometheus.internal), optional PROMETHEUS_TOKEN (bearer).
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--hours", type=float, default=72)
    ap.add_argument("--step", default="1h")
    args = ap.parse_args()

    base = os.environ.get("PROMETHEUS_URL")
    if not base:
        print("prometheus_query.py: PROMETHEUS_URL is not set", file=sys.stderr)
        return 2

    end = time.time()
    params = urllib.parse.urlencode({"query": args.query, "start": end - args.hours * 3600,
                                     "end": end, "step": args.step})
    req = urllib.request.Request(f"{base.rstrip('/')}/api/v1/query_range?{params}")
    if token := os.environ.get("PROMETHEUS_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)

    result = body.get("data", {}).get("result", [])
    values = result[0]["values"] if result else []
    series = [{"t": ts, "v": float(v)} for ts, v in values if v not in ("NaN", "+Inf", "-Inf")]
    json.dump(series, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
