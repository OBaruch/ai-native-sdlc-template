#!/usr/bin/env bash
# Behavioral tests for .claude/hooks. Run: make hook-test
# Hooks run against a throw-away project dir, so markers and logs never touch the real repo.
# Fixture values that look like commands or credentials are assembled at runtime.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS="$REPO/.claude/hooks"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.claude"
export CLAUDE_PROJECT_DIR="$TMP"

pass=0
fail=0

# expect <name> <hook> <expected: allow|block|ask> <json>
expect() {
  local name="$1" hook="$2" want="$3" json="$4" out rc got
  out="$(printf '%s' "$json" | bash "$HOOKS/$hook" 2>&1)"
  rc=$?
  if [[ $rc -eq 2 ]]; then got=block
  elif [[ $rc -eq 0 && "$out" == *'"permissionDecision":"ask"'* ]]; then got=ask
  elif [[ $rc -eq 0 && "$out" == *'"decision":"block"'* ]]; then got=block
  elif [[ $rc -eq 0 ]]; then got=allow
  else got="error($rc)"; fi
  if [[ "$got" == "$want" ]]; then
    pass=$((pass + 1)); printf '  ok    %-45s %s\n' "$name" "$got"
  else
    fail=$((fail + 1)); printf '  FAIL  %-45s want=%s got=%s  %s\n' "$name" "$want" "$got" "${out:0:120}"
  fi
}

PROD="produc""tion"
DEPLOY="./scripts/deploy.sh $PROD"
AWS_KEY="AKIA""ABCDEFGHIJKLMNOP"
PW_LINE="password = \\\"hunter2hunter2\\\""

echo "production-gate"
expect "prod deploy without approval"        production-gate.sh block "{\"tool_input\":{\"command\":\"$DEPLOY\"}}"
RELEASE_APPROVAL=CHG-42 \
expect "prod deploy with ticket"             production-gate.sh allow "{\"tool_input\":{\"command\":\"$DEPLOY\"}}"
RELEASE_APPROVAL=yes \
expect "prod apply with invalid ticket"      production-gate.sh block "{\"tool_input\":{\"command\":\"kubectl apply -f prod/\"}}"
expect "staging deploy"                      production-gate.sh allow '{"tool_input":{"command":"./scripts/deploy.sh staging"}}'
expect "word containing prod (build:product)" production-gate.sh allow '{"tool_input":{"command":"npm run build:product"}}'
expect "malformed input fails closed"        production-gate.sh block 'not json'
expect "commit message mentioning it"        production-gate.sh allow "{\"tool_input\":{\"command\":\"git commit -m 'fix $PROD deploy gate'\"}}"
expect "heredoc commit body mentioning it"   production-gate.sh allow "{\"tool_input\":{\"command\":\"git commit -F - <<'EOF'\\nnotes: $PROD deploy gate\\nEOF\"}}"
expect "deploy chained after a commit"       production-gate.sh block "{\"tool_input\":{\"command\":\"git commit -m x && $DEPLOY\"}}"
expect "workflow dispatch to $PROD"          production-gate.sh block "{\"tool_input\":{\"command\":\"gh workflow run deploy.yml -f environment=$PROD\"}}"

echo "protected-paths"
expect "generated code (absolute path)"      protected-paths.sh block "{\"tool_input\":{\"file_path\":\"$TMP/src/gen/x.ts\"}}"
expect "migration without ticket"            protected-paths.sh block '{"tool_input":{"file_path":"migrations/001.sql"}}'
CHANGE_TICKET=CHG-7 \
expect "migration with ticket"               protected-paths.sh allow '{"tool_input":{"file_path":"migrations/001.sql"}}'
expect "guardrail file asks a human"         protected-paths.sh ask   '{"tool_input":{"file_path":".claude/hooks/lib.sh"}}'
expect "normal source file"                  protected-paths.sh allow '{"tool_input":{"file_path":"src/app.ts"}}'

echo "block-secrets"
expect "cloud access key in content"         block-secrets.sh block "{\"tool_input\":{\"file_path\":\"src/a.py\",\"content\":\"k = '$AWS_KEY'\"}}"
expect "password literal in edit"            block-secrets.sh block "{\"tool_input\":{\"file_path\":\"src/a.py\",\"new_string\":\"$PW_LINE\"}}"
expect "writing .env"                        block-secrets.sh block '{"tool_input":{"file_path":".env","content":"X=1"}}'
expect "writing .env.example"                block-secrets.sh allow '{"tool_input":{"file_path":".env.example","content":"X=changeme"}}'
expect "secret read from environment"        block-secrets.sh allow '{"tool_input":{"file_path":"src/a.py","content":"x = os.environ[\"TOKEN\"]"}}'

echo "protect-tests"
expect "edit test outside a fix task"        protect-tests.sh allow '{"tool_name":"Edit","tool_input":{"file_path":"tests/test_a.py"}}'
touch "$TMP/.claude/fix-task"
expect "edit test during fix task"           protect-tests.sh block '{"tool_name":"Edit","tool_input":{"file_path":"tests/test_a.py"}}'
expect "sed -i on test during fix task"      protect-tests.sh block '{"tool_name":"Bash","tool_input":{"command":"sed -i s/1/2/ tests/test_a.py"}}'
expect "removing the marker"                 protect-tests.sh block '{"tool_name":"Bash","tool_input":{"command":"rm .claude/fix-task"}}'
expect "edit source during fix task"         protect-tests.sh allow '{"tool_name":"Edit","tool_input":{"file_path":"src/a.py"}}'
expect "run tests during fix task"           protect-tests.sh allow '{"tool_name":"Bash","tool_input":{"command":"make test"}}'
rm -f "$TMP/.claude/fix-task"

echo "plan-sync / require-verification / format-lint"
expect "commit without active change"        plan-sync.sh allow '{"tool_input":{"command":"git commit -m x"}}'
expect "stop outside a git repo"             require-verification.sh allow '{"stop_hook_active":false,"transcript_path":""}'
expect "stop when already re-prompted"       require-verification.sh allow '{"stop_hook_active":true}'
expect "format a missing file"               format-lint.sh allow '{"tool_input":{"file_path":"nope.py"}}'

echo
echo "hook tests: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
