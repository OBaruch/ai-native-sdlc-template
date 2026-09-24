#!/usr/bin/env bash
# Keeps credentials out of the diff.
# Event: PreToolUse / Edit|Write|MultiEdit|NotebookEdit.
set -uo pipefail
. "$(dirname "$0")/lib.sh"

path="$(rel_path "$(json_get .tool_input.file_path)")"

# This file defines the patterns, so it is allowed to contain them.
[[ "$path" == ".claude/hooks/block-secrets.sh" ]] && exit 0

case "$path" in
  .env|.env.*|*/.env|*/.env.*)
    [[ "$path" == *.env.example ]] || block "$path holds secrets and must not be written by the agent. Use .env.example with placeholder values." ;;
  *.pem|*.key|*.p12|*.pfx|*id_rsa*|*id_ed25519*)
    block "$path looks like a private key file. Keys are provisioned by the platform team, never committed." ;;
esac

content="$(json_get .tool_input.content)$(json_get .tool_input.new_string)$(json_get .tool_input.edits)$(json_get .tool_input.new_source)"
[[ -z "$content" ]] && exit 0

# Add your organization's token formats here.
patterns=(
  'AKIA[0-9A-Z]{16}'                                   # AWS access key id
  '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----'              # PEM private key
  'gh[pousr]_[A-Za-z0-9]{36,}'                         # GitHub token
  'github_pat_[A-Za-z0-9_]{40,}'                       # GitHub fine-grained token
  'sk-ant-[A-Za-z0-9_-]{20,}'                          # Anthropic API key
  'xox[abprs]-[A-Za-z0-9-]{10,}'                       # Slack token
  'AIza[0-9A-Za-z_-]{35}'                              # Google API key
  '(password|passwd|secret|api[_-]?key|access[_-]?token)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"'$<{]{8,}["'"'"']'
)

for re in "${patterns[@]}"; do
  if printf '%s' "$content" | grep -Eiq -- "$re"; then
    audit "block secret pattern in ${path:-<unknown>}"
    block "the change to ${path:-this file} appears to contain a credential (pattern: $re). Read it from the environment or the secret manager instead. If it is a false positive, ask the engineer to adjust .claude/hooks/block-secrets.sh."
  fi
done
exit 0
