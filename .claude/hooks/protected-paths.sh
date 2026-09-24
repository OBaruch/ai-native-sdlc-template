#!/usr/bin/env bash
# Build-time guardrail + gate G2 (governance/approval-gates.md).
# Event: PreToolUse / Edit|Write|MultiEdit|NotebookEdit. Fast and scoped to one file.
#   - generated code          -> always blocked (change the generator instead)
#   - frozen packages         -> always blocked
#   - migrations / infra      -> blocked unless CHANGE_TICKET is set for the session
#   - the guardrails themselves -> a human must approve the edit
set -uo pipefail
. "$(dirname "$0")/lib.sh"

# ---- customise these lists -------------------------------------------------
GENERATED=("src/gen/" "*/generated/*")
FROZEN=()                                   # e.g. ("src/legacy/v1/")
NEEDS_TICKET=("migrations/" "*/migrations/*" "infra/" "terraform/" "k8s/")
GUARDRAILS=(".claude/hooks/" ".claude/settings.json" "managed-settings/" ".github/CODEOWNERS" "REVIEW.md" ".github/workflows/")
# -----------------------------------------------------------------------------

path="$(rel_path "$(json_get .tool_input.file_path)")"
[[ -z "$path" ]] && path="$(rel_path "$(json_get .tool_input.notebook_path)")"
[[ -z "$path" ]] && exit 0

matches() { # matches <path> <pattern...>
  local p="$1"; shift
  local pat
  for pat in "$@"; do
    [[ -z "$pat" ]] && continue
    if [[ "$pat" == *"*"* ]]; then
      # shellcheck disable=SC2053
      [[ "$p" == $pat ]] && return 0
    else
      [[ "$p" == "$pat"* ]] && return 0
    fi
  done
  return 1
}

if matches "$path" "${GENERATED[@]}"; then
  audit "block generated: $path"
  block "$path is generated code. Change the generator or schema and regenerate instead."
fi

if (( ${#FROZEN[@]} )) && matches "$path" "${FROZEN[@]}"; then
  audit "block frozen: $path"
  block "$path is in a frozen package. Make the change in its successor (see CLAUDE.md > Architecture)."
fi

if matches "$path" "${NEEDS_TICKET[@]}"; then
  if [[ -z "${CHANGE_TICKET:-}" ]]; then
    audit "block no-ticket: $path"
    block "$path needs an approved change ticket (gate G2). Get one from change management, then restart the session with CHANGE_TICKET=<id>."
  fi
  audit "allow ticket=$CHANGE_TICKET: $path"
fi

if matches "$path" "${GUARDRAILS[@]}"; then
  audit "ask guardrail: $path"
  ask "Editing $path changes the guardrails themselves. A human must approve this edit; the PR also needs code owner review."
fi

exit 0
