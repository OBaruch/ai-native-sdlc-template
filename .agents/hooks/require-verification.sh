#!/usr/bin/env bash
# Finalize only when verification covers the current working tree.
set -uo pipefail
. "$(dirname "$0")/lib.sh"
VERIFY_SCRIPT="$(cd "$(dirname "$0")/../.." && pwd)/scripts/verify.py"
if ! (cd "$PROJECT_ROOT" && python3 "$VERIFY_SCRIPT" --check); then
  block 'Changes need current verification evidence. Run python3 scripts/verify.py (or --template for the scaffold), then fix all failures. See AGENTS.md.'
fi
