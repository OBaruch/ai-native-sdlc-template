#!/usr/bin/env bash
# "Done" means verified. If the session changed code but never ran the verification
# commands, Claude is sent back to run them before it may finish.
# Event: Stop.
set -uo pipefail
. "$(dirname "$0")/lib.sh"

# Avoid loops: if we already sent Claude back once, let it stop.
[[ "$(json_get .stop_hook_active)" == "true" ]] && exit 0

changed="$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null \
  | sed -E 's/^.{3}//; s/.* -> //' \
  | grep -Ev '\.(md|txt)$|^(intent|doc|docs|postmortems)/|^\.claude/' \
  | head -1)"
[[ -z "$changed" ]] && exit 0

transcript="$(json_get .transcript_path)"
if [[ -n "$transcript" && -f "$transcript" ]] \
   && grep -Eq '"command":[[:space:]]*"[^"]*make (check|test)' "$transcript"; then
  exit 0
fi

audit "block stop-without-verification: $changed"
printf '%s\n' '{"decision":"block","reason":"Code changed but make test / make check was not run in this session. Run make lint, make test and make build, paste the output, and fix any failure before reporting the task complete (CLAUDE.md > Verifying your work)."}'
exit 0
