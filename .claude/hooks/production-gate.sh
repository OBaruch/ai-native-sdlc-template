#!/usr/bin/env bash
# Gate G3 (governance/approval-gates.md): production releases need a named authorization.
# Event: PreToolUse / Bash.
#
# Approval = RELEASE_APPROVAL set in the environment Claude Code was started with,
# holding the release ticket id (e.g. CHG-1234). A variable written inside the command
# itself does not count: the hook only reads its own environment.
#
# In regulated setups, register this gate in managed settings instead
# (managed-settings/managed-settings.json), so engineers cannot switch it off.
set -uo pipefail
. "$(dirname "$0")/lib.sh"

TICKET_PATTERN='^[A-Z][A-Z0-9]+-[0-9]+$'   # adjust to your change-ticket format

cmd="$(json_get .tool_input.command)"
[[ -z "$cmd" ]] && exit 0

# Heredoc bodies (commit messages, PR bodies) are text, not commands: drop them.
strip_heredocs() {
  local out="" delim="" line trimmed
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ -n "$delim" ]]; then
      trimmed="${line#"${line%%[![:space:]]*}"}"
      [[ "$trimmed" == "$delim" ]] && delim=""
      continue
    fi
    if [[ "$line" =~ \<\<-?[[:space:]]*[\'\"]?([A-Za-z_][A-Za-z0-9_]*)[\'\"]? ]]; then
      delim="${BASH_REMATCH[1]}"
    fi
    out+="$line"$'\n'
  done <<< "$1"
  printf '%s' "$out"
}

# Commands that only write text or read state; a deploy chained after them is still checked.
exempt_re='^(git[[:space:]]+(commit|tag|log|show|diff|status|add|notes)|gh[[:space:]]+(pr|issue|repo|label|search)|echo|printf|grep|rg|cat|head|tail|less)([[:space:]]|$)'
action_re='(deploy|release|rollout|promote|rollback|helm[[:space:]]+upgrade|kubectl[[:space:]]+apply|terraform[[:space:]]+apply)'
target_re='(^|[^a-z])(prod|production|prd)([^a-z]|$)'

shopt -s nocasematch
hit=""
while IFS= read -r segment; do
  segment="${segment#"${segment%%[![:space:]]*}"}"
  [[ -z "$segment" ]] && continue
  [[ "$segment" =~ $exempt_re ]] && continue
  if [[ "$segment" =~ $action_re ]] && [[ "$segment" =~ $target_re ]]; then
    hit="$segment"; break
  fi
done < <(strip_heredocs "$cmd" | sed -E 's/(&&|\|\||;|\|)/\n/g')

if [[ -n "$hit" ]]; then
  approval="${RELEASE_APPROVAL:-}"
  if [[ -z "$approval" ]]; then
    audit "block no-approval: $cmd"
    block "production changes need a release authorization. Ask the release manager (see governance/approval-gates.md, gate G3) for a ticket, then restart the session with RELEASE_APPROVAL=<ticket-id>. Until then, prepare the release and stop at this gate."
  fi
  shopt -u nocasematch
  if ! [[ "$approval" =~ $TICKET_PATTERN ]]; then
    audit "block bad-ticket=$approval: $cmd"
    block "RELEASE_APPROVAL='$approval' is not a valid ticket id (expected something like CHG-1234)."
  fi
  audit "allow ticket=$approval: $cmd"
fi
exit 0
