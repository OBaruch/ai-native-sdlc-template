#!/usr/bin/env bash
# Shared helpers for the hooks in this folder. Source it, do not run it:
#   . "$(dirname "$0")/lib.sh"
#
# Canonical policy event: JSON with phase and operation on stdin.
#   exit 0  -> allow
#   exit 2  -> block; stderr is shown to the agent so it can explain / re-route
#   JSON on stdout with decision "ask" -> pause for a human

HOOK_INPUT="$(cat)"
PROJECT_ROOT="${SDLC_PROJECT_DIR:-$PWD}"

# Guardrails must fail CLOSED: if the event cannot be parsed, the action is blocked.
# Pick a JSON parser that actually runs (on Windows `python3` may be a Store stub on PATH).
JSON_PARSER=""
if command -v jq >/dev/null 2>&1 && printf '{}' | jq -e . >/dev/null 2>&1; then
  JSON_PARSER="jq"
else
  for _c in python3 python py; do
    if command -v "$_c" >/dev/null 2>&1 && "$_c" -c 'import json' >/dev/null 2>&1; then
      JSON_PARSER="$_c"; break
    fi
  done
fi
if [[ -z "$JSON_PARSER" ]]; then
  echo "BLOCKED by $(basename "$0"): no working JSON parser (jq or Python), so this guardrail cannot evaluate the action. Install jq or Python." >&2
  exit 2
fi
if [[ "$JSON_PARSER" == "jq" ]]; then
  printf '%s' "$HOOK_INPUT" | jq -e . >/dev/null 2>&1 || { echo "BLOCKED by $(basename "$0"): unreadable hook input." >&2; exit 2; }
else
  printf '%s' "$HOOK_INPUT" | "$JSON_PARSER" -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1 \
    || { echo "BLOCKED by $(basename "$0"): unreadable hook input." >&2; exit 2; }
fi

# json_get .operation.command  -> prints the value ("" when missing).
json_get() {
  local path="$1"
  if [[ "$JSON_PARSER" == "jq" ]]; then
    printf '%s' "$HOOK_INPUT" | jq -r "$path // empty | if type == \"string\" then . else tojson end"
    return
  fi
  printf '%s' "$HOOK_INPUT" | "$JSON_PARSER" -c '
import json, sys
data = json.load(sys.stdin)
for key in sys.argv[1].lstrip(".").split("."):
    data = data.get(key) if isinstance(data, dict) else None
if data is None:
    print("", end="")
elif isinstance(data, str):
    print(data, end="")
else:
    print(json.dumps(data), end="")
' "$path"
}

# Path relative to the project root, with forward slashes (works for Windows paths too).
rel_path() {
  local p="${1//\\//}" root="${PROJECT_ROOT//\\//}"
  local lp="${p,,}" lroot="${root,,}"
  if [[ "$lp" == "$lroot/"* ]]; then
    p="${p:${#root}+1}"
  fi
  printf '%s' "$p"
}

# Emit a harness-independent policy decision.
decide() {
  python3 -c 'import json,sys; print(json.dumps({"decision":sys.argv[1],"reason":sys.argv[2]}))' "$1" "$2"
}
block() { decide deny "$*"; exit 2; }
ask() { decide ask "$*"; exit 0; }

# Append an audit line (hook decisions are also exported via OpenTelemetry when enabled).
audit() {
  local dir="$PROJECT_ROOT/.agents/logs"
  mkdir -p "$dir" 2>/dev/null || return 0
  printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(basename "$0")" "$*" >> "$dir/hooks.log" 2>/dev/null || true
}
