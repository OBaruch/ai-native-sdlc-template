#!/usr/bin/env bash
# Portable response orchestration. The selected agent proposes; humans approve.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/respond.py" "$@"
