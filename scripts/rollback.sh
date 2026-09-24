#!/usr/bin/env bash
# One-command rollback. Rehearsed weekly in staging (.github/workflows/rollback-drill.yml)
# and invoked by the maintain loop through the rollback-deploy runbook.
#   usage: scripts/rollback.sh <dev|staging|production> [<version-to-restore>]
# Without a version it restores the previous successful release.
set -euo pipefail

ENV_NAME="${1:?usage: rollback.sh <env> [<version>]}"
TARGET="${2:-}"

# ---- TEMPLATE: replace with your platform's commands ---------------------------
previous_version() { echo "TODO: print the previous successful release for '$ENV_NAME'" >&2; return 1; }
rollback_cmd()     { echo "TODO: roll '$ENV_NAME' back to '$1' (helm rollback / redeploy tag / flip traffic)"; return 1; }
# ---------------------------------------------------------------------------------

if [[ "$ENV_NAME" == "production" && -z "${RELEASE_APPROVAL:-}" ]]; then
  echo "rollback.sh: production rollback needs RELEASE_APPROVAL=<ticket> (or the CI production environment approval)." >&2
  exit 2
fi

version="${TARGET:-$(previous_version)}"
echo "Rolling back $ENV_NAME to $version"
rollback_cmd "$version"
"$(dirname "$0")/deploy.sh" "$ENV_NAME" --health-only
