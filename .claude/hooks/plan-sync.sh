#!/usr/bin/env bash
# Keeps plan.md in step with the code. When a change is active and a commit stages code
# but not the change's plan.md, a human confirms the implementation still matches the plan.
# Event: PreToolUse / Bash (only reacts to `git commit`).
#
# Activate for a change with:  echo intent/0007-my-change > .claude/active-change
set -uo pipefail
. "$(dirname "$0")/lib.sh"

cmd="$(json_get .tool_input.command)"
[[ "$cmd" =~ git[[:space:]]+commit ]] || exit 0

active_file="$PROJECT_ROOT/.claude/active-change"
[[ -f "$active_file" ]] || exit 0
change_dir="$(tr -d '\r\n' < "$active_file")"
change_dir="${change_dir%/}"
[[ -n "$change_dir" ]] || exit 0

staged="$(git -C "$PROJECT_ROOT" diff --cached --name-only 2>/dev/null)"
code="$(printf '%s\n' "$staged" | grep -Ev '^(intent/|doc/|docs/|postmortems/)|\.md$' | grep -v '^$' | head -1)"
plan="$(printf '%s\n' "$staged" | grep -Fx "$change_dir/plan.md")"

if [[ -n "$code" && -z "$plan" ]]; then
  audit "ask plan-sync: $change_dir"
  ask "Code is staged but $change_dir/plan.md is not. If the implementation departed from the plan, update plan.md in this same commit. Approve only if the plan is still accurate."
fi
exit 0
