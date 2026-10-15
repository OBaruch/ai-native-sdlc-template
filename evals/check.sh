#!/usr/bin/env bash
# Grades one eval run.
#   usage: evals/check.sh <eval.json> <result.json> [workdir]
# Each check in the eval is either:
#   { "name": ..., "run": "<shell command>" }                 -> passes when it exits 0 (run in workdir)
#   { "name": ..., "result_field": "<key>", "equals": <v> }  -> compares a field of the normalized JSON result
# Exit 0 = every check passed.
set -uo pipefail

eval_file="$1"
result_file="$2"
workdir="${3:-.}"
PY="$(for c in python3 python py; do "$c" -c 'import json' >/dev/null 2>&1 && { echo "$c"; break; }; done)"
[[ -n "$PY" ]] || { echo "check.sh: no working python found" >&2; exit 1; }

checks_tsv="$("$PY" - "$eval_file" "$result_file" <<'PY'
import json, sys
spec = json.load(open(sys.argv[1], encoding="utf-8"))
try:
    result = json.load(open(sys.argv[2], encoding="utf-8"))
except Exception:
    result = {}
for c in spec.get("checks", []):
    name = c.get("name", "unnamed").replace("\t", " ")
    if "run" in c:
        print(f"run\t{name}\t{c['run']}")
    elif "result_field" in c:
        ok = result.get(c["result_field"]) == c.get("equals")
        print(f"field\t{name}\t{'1' if ok else '0'}")
PY
)"

pass=0
fail=0
while IFS=$'\t' read -r kind name payload; do
  [[ -z "$kind" ]] && continue
  if [[ "$kind" == "run" ]]; then
    if (cd "$workdir" && bash -c "$payload") >/dev/null 2>&1; then ok=1; else ok=0; fi
  else
    ok="$payload"
  fi
  if [[ "$ok" == "1" ]]; then
    echo "  PASS  $name"; pass=$((pass + 1))
  else
    echo "  FAIL  $name"; fail=$((fail + 1))
  fi
done <<< "$checks_tsv"

echo "  -> $pass passed, $fail failed"
[[ $fail -eq 0 && $pass -gt 0 ]]
