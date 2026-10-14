#!/usr/bin/env bash
# Harness-neutral eval entry point. See evals/README.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/run_evals.py" "$@"
