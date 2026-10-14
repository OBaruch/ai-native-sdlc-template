#!/usr/bin/env bash
# Single entry point for deployments, used by humans, CI and (through MCP/CI) the agent.
#   usage: scripts/deploy.sh <dev|staging|production> [<version>] | <env> --health-only
#
# Production requires RELEASE_APPROVAL (a release ticket). In CI the "production" GitHub
# environment additionally requires a named reviewer. Defense in depth: the local
# production-gate hook enforces the same rule for harnesses with a policy-event adapter.
set -euo pipefail

ENV_NAME="${1:?usage: deploy.sh <env> [<version>|--health-only]}"
ARG="${2:-}"

# ---- TEMPLATE: replace with your platform's commands ---------------------------
deploy_cmd()  { echo "TODO: deploy version '$1' to '$ENV_NAME' (helm/kubectl/terraform/cloud CLI)"; return 1; }
health_cmd()  { echo "TODO: health check for '$ENV_NAME' (curl -fsS https://<host>/health)"; return 1; }
# ---------------------------------------------------------------------------------

case "$ENV_NAME" in
  dev|staging) ;;
  production)
    if [[ -z "${RELEASE_APPROVAL:-}" ]]; then
      echo "deploy.sh: production needs RELEASE_APPROVAL=<release ticket> (governance/approval-gates.md, gate G3)." >&2
      exit 2
    fi ;;
  *) echo "deploy.sh: unknown environment '$ENV_NAME'" >&2; exit 2 ;;
esac

if [[ "$ARG" == "--health-only" ]]; then
  health_cmd
  exit $?
fi

version="${ARG:-$(git rev-parse HEAD)}"
echo "Deploying $version to $ENV_NAME (approval: ${RELEASE_APPROVAL:-n/a})"
deploy_cmd "$version"
health_cmd
