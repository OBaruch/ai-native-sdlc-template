#!/usr/bin/env python3
"""Median PR cycle time (hours from open to merge) per merge day, oldest first.

Prints a JSON list of {"t": "YYYY-MM-DD", "v": median_hours}. Needs `gh` authenticated.
"""

import argparse
import collections
import datetime as dt
import json
import statistics
import subprocess
import sys


def parse(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()

    since = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
    out = subprocess.run(
        ["gh", "pr", "list", "--state", "merged", "--limit", str(args.limit),
         "--search", f"merged:>={since}", "--json", "createdAt,mergedAt"],
        capture_output=True, text=True, check=True).stdout
    by_day: dict = collections.defaultdict(list)
    for pr in json.loads(out or "[]"):
        if not pr.get("mergedAt"):
            continue
        merged = parse(pr["mergedAt"])
        by_day[merged.date()].append((merged - parse(pr["createdAt"])).total_seconds() / 3600)

    series = [{"t": d.isoformat(), "v": round(statistics.median(v), 2)} for d, v in sorted(by_day.items())]
    json.dump(series, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
