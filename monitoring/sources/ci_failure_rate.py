#!/usr/bin/env python3
"""Daily CI failure rate on the default branch, oldest day first, from the GitHub CLI.

Prints a JSON list of {"t": "YYYY-MM-DD", "v": failure_rate}. Days without completed runs
are skipped. Needs `gh` authenticated (GH_TOKEN in CI).
"""

import argparse
import collections
import datetime as dt
import json
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=45)
    ap.add_argument("--workflow", default=None, help="workflow name or file, e.g. CI or ci.yml")
    ap.add_argument("--branch", default=None, help="defaults to the repository's default branch")
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()

    branch = args.branch or subprocess.run(
        ["gh", "repo", "view", "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"],
        capture_output=True, text=True, check=True).stdout.strip()

    cmd = ["gh", "run", "list", "--branch", branch, "--limit", str(args.limit),
           "--json", "conclusion,createdAt,status"]
    if args.workflow:
        cmd += ["--workflow", args.workflow]
    runs = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout or "[]")

    since = dt.date.today() - dt.timedelta(days=args.days)
    total: collections.Counter = collections.Counter()
    failed: collections.Counter = collections.Counter()
    for run in runs:
        if run.get("status") != "completed" or run.get("conclusion") in ("cancelled", "skipped"):
            continue
        day = dt.date.fromisoformat(run["createdAt"][:10])
        if day < since:
            continue
        total[day] += 1
        if run.get("conclusion") in ("failure", "timed_out", "startup_failure"):
            failed[day] += 1

    series = [{"t": d.isoformat(), "v": round(failed[d] / total[d], 4)} for d in sorted(total)]
    json.dump(series, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
