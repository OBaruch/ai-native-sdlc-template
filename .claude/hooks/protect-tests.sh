#!/usr/bin/env bash
# Protects the feedback loop: during a bug-fix task the agent must not weaken the test
# that proves the fix. Active only while .claude/fix-task exists (or FIX_TASK=1).
# Event: PreToolUse / Bash and Edit|Write|MultiEdit|NotebookEdit.
#
# Workflow (see .claude/commands/fix-bug.md):
#   1. write the failing test, confirm it fails for the expected reason, commit it
#   2. a human creates the marker:  touch .claude/fix-task
#   3. Claude fixes the code; test files are read-only
#   4. a human removes the marker when the fix is merged
set -uo pipefail
. "$(dirname "$0")/lib.sh"

MARKER="$PROJECT_ROOT/.claude/fix-task"
[[ -f "$MARKER" || "${FIX_TASK:-}" == "1" ]] || exit 0

# Customise to your test layout.
is_test_path() {
  case "$1" in
    tests/*|*/tests/*|test/*|*/test/*|__tests__/*|*/__tests__/*) return 0 ;;
    *_test.*|*.test.*|*.spec.*|test_*|*/test_*|*Test.java|*Tests.cs) return 0 ;;
    *conftest.py|*jest.config.*|*pytest.ini|*vitest.config.*) return 0 ;;
  esac
  return 1
}

tool="$(json_get .tool_name)"

if [[ "$tool" == "Bash" ]]; then
  cmd="$(json_get .tool_input.command)"
  if [[ "$cmd" == *"fix-task"* ]]; then
    audit "block marker-tamper: $cmd"
    block "the fix-task marker can only be changed by a human."
  fi
  # Heuristic: a write-ish shell command that names a test path.
  if [[ "$cmd" =~ (sed[[:space:]]+-i|perl[[:space:]]+-pi|>|tee|mv[[:space:]]|rm[[:space:]]|cp[[:space:]]|git[[:space:]]+(checkout|restore|rm)) ]]; then
    for word in $cmd; do
      word="${word//\"/}"; word="${word//\'/}"
      if is_test_path "$(rel_path "$word")"; then
        audit "block bash-test-edit: $cmd"
        block "this is a fix task: test files are read-only. Fix the code so the committed test passes."
      fi
    done
  fi
  exit 0
fi

path="$(rel_path "$(json_get .tool_input.file_path)")"
[[ -z "$path" ]] && path="$(rel_path "$(json_get .tool_input.notebook_path)")"
if [[ -n "$path" ]] && is_test_path "$path"; then
  audit "block test-edit: $path"
  block "this is a fix task: $path is read-only. Fix the code, not the test. If the test itself is wrong, stop and tell the engineer."
fi
exit 0
