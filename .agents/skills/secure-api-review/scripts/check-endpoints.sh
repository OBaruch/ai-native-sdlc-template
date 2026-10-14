#!/usr/bin/env bash
# Static smoke check for the secure-api-review skill.
# Finds route definitions and flags ones without an auth marker nearby.
# It is a tripwire, not a proof: the PR review re-checks the policy.
#
# Customise the three patterns for your framework, e.g.
#   Express:  ROUTE_RE='\.(get|post|put|patch|delete)\(' AUTH_RE='requireAuth|authenticate'
#   FastAPI:  ROUTE_RE='@(app|router)\.(get|post|put|patch|delete)' AUTH_RE='Depends\(.*auth'
#   Spring:   ROUTE_RE='@(Get|Post|Put|Patch|Delete)Mapping' AUTH_RE='@PreAuthorize|@Secured'
set -uo pipefail

SRC_DIR="${SRC_DIR:-src}"
ROUTE_RE="${ROUTE_RE:-\.(get|post|put|patch|delete)\(|@(app|router)\.(get|post|put|patch|delete)|@(Get|Post|Put|Patch|Delete)Mapping}"
AUTH_RE="${AUTH_RE:-auth|Authorize|Secured|login_required|requireUser}"
PUBLIC_RE="${PUBLIC_RE:-/health|/ready|/metrics}"
CONTEXT_LINES="${CONTEXT_LINES:-3}"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "check-endpoints: no $SRC_DIR/ directory, nothing to check."
  exit 0
fi

findings=0
total=0
while IFS=: read -r file line _; do
  [[ -z "$file" ]] && continue
  total=$((total + 1))
  start=$(( line > CONTEXT_LINES ? line - CONTEXT_LINES : 1 ))
  window="$(sed -n "${start},$((line + CONTEXT_LINES))p" "$file")"
  if printf '%s' "$window" | grep -Eq "$PUBLIC_RE"; then
    continue
  fi
  if ! printf '%s' "$window" | grep -Eq "$AUTH_RE"; then
    echo "FINDING  $file:$line  route without an auth marker within ${CONTEXT_LINES} lines"
    findings=$((findings + 1))
  fi
done < <(grep -rEn --include='*.*' "$ROUTE_RE" "$SRC_DIR" 2>/dev/null | grep -v '/gen/')

echo "check-endpoints: $total route(s) scanned, $findings finding(s)."
[[ $findings -eq 0 ]]
