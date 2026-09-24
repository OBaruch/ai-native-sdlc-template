#!/usr/bin/env bash
# Runs the agent eval suite. Each enabled eval runs in its own throw-away git worktree,
# non-interactively, and is graded by evals/check.sh.
#
# Env:
#   EVAL_PASS_THRESHOLD  minimum pass rate, 0..1 (default 0.9)
#   EVAL_FILTER          glob of eval files to run (default evals/*.json)
#   ANTHROPIC_API_KEY    required by claude
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
THRESHOLD="${EVAL_PASS_THRESHOLD:-0.9}"
PY="$(for c in python3 python py; do "$c" -c 'import json' >/dev/null 2>&1 && { echo "$c"; break; }; done)"
[[ -n "$PY" ]] || { echo "run.sh: no working python found" >&2; exit 1; }
RUNS="$ROOT/evals/.runs"
mkdir -p "$RUNS"
summary="$RUNS/summary.md"
printf '| Eval | Source | Result |\n|---|---|---|\n' > "$summary"

field() { "$PY" -c 'import json,sys; v=json.load(open(sys.argv[1],encoding="utf-8")).get(sys.argv[2],sys.argv[3]); print(str(v).lower() if isinstance(v,bool) else v)' "$@"; }

total=0
passed=0
for eval_file in ${EVAL_FILTER:-evals/*.json}; do
  [[ -f "$eval_file" ]] || continue
  [[ "$(field "$eval_file" enabled true)" == "true" ]] || { echo "skip  $eval_file (disabled)"; continue; }

  id="$(field "$eval_file" id "$(basename "$eval_file" .json)")"
  base="$(field "$eval_file" base_ref HEAD)"
  tools="$(field "$eval_file" allowed_tools "Read,Grep,Glob")"
  turns="$(field "$eval_file" max_turns 30)"
  source="$(field "$eval_file" source task)"
  prompt="$(field "$eval_file" prompt "")"
  wt="$RUNS/wt-$id"

  echo "run   $id"
  total=$((total + 1))
  git worktree remove --force "$wt" >/dev/null 2>&1 || true
  git worktree add --detach "$wt" "$base" >/dev/null

  (cd "$wt" && claude -p "$prompt" --allowedTools "$tools" --max-turns "$turns" --output-format json) \
    > "$RUNS/$id.result.json" 2> "$RUNS/$id.stderr.log" || true

  if bash evals/check.sh "$eval_file" "$RUNS/$id.result.json" "$wt"; then
    passed=$((passed + 1)); verdict="pass"
  else
    verdict="**fail**"
  fi
  printf '| %s | %s | %s |\n' "$id" "$source" "$verdict" >> "$summary"
  git worktree remove --force "$wt" >/dev/null 2>&1 || true
done

if [[ $total -eq 0 ]]; then
  echo "No enabled evals. Add 20-50 real tasks to evals/ and set \"enabled\": true." | tee -a "$summary"
  [[ -n "${GITHUB_STEP_SUMMARY:-}" ]] && cat "$summary" >> "$GITHUB_STEP_SUMMARY"
  exit 0
fi

rate="$("$PY" -c "print(round($passed/$total, 3))")"
line="Pass rate: $passed/$total = $rate (threshold $THRESHOLD)"
echo "$line"
printf '\n%s\n' "$line" >> "$summary"
[[ -n "${GITHUB_STEP_SUMMARY:-}" ]] && cat "$summary" >> "$GITHUB_STEP_SUMMARY"

"$PY" -c "import sys; sys.exit(0 if $rate >= $THRESHOLD else 1)" || {
  echo "Eval pass rate below threshold: this configuration change needs review before merge." >&2
  exit 1
}
