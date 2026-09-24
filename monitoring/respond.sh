#!/usr/bin/env bash
# Turns actionable findings from detect.py into gated work. Runs stateless in CI.
#   usage: monitoring/respond.sh findings.json
#
# diagnose (2σ): Claude investigates with read-only tools and returns an intent.md,
#                which this script commits on a branch and opens as a PR for triage.
# propose  (3σ): same, and Claude may also prepare a minimal fix in the working tree
#                (included in the PR). Runbook routes trigger only runbooks listed in bands.yaml.
# report   (3σ on process metrics): a report PR for engineering leadership.
#
# Claude never merges, never deploys directly, and never gets production credentials.
set -euo pipefail

FINDINGS="${1:-findings.json}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
PY="$(for c in python3 python py; do "$c" -c 'import json' >/dev/null 2>&1 && { echo "$c"; break; }; done)"
[[ -n "$PY" ]] || { echo "respond.sh: no working python found" >&2; exit 1; }
DEFAULT_BRANCH="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || echo main)"

# jget '<python expression over d>' < file.json   (trusted expressions from this script only)
jget() { "$PY" -c 'import json,sys; d=json.load(sys.stdin); print(eval(sys.argv[1], {"json": json}, {"d": d}))' "$1"; }

next_intent_number() {
  local max
  max="$(ls -d intent/[0-9][0-9][0-9][0-9]-* 2>/dev/null | sed -E 's@intent/([0-9]{4}).*@\1@' | sort -n | tail -1)"
  printf '%04d' $(( 10#${max:-0} + 1 ))
}

count="$(jget 'len([f for f in d["findings"] if f["action"] in ("diagnose","propose","report")])' < "$FINDINGS")"
[[ "$count" == "0" ]] && { echo "respond: nothing actionable."; exit 0; }

for i in $(seq 0 $(( $(jget 'len(d["findings"])' < "$FINDINGS") - 1 ))); do
  f="$(jget "json.dumps(d['findings'][$i])" < "$FINDINGS")"
  action="$(printf '%s' "$f" | jget 'd["action"]')"
  [[ "$action" =~ ^(diagnose|propose|report)$ ]] || continue

  metric="$(printf '%s' "$f" | jget 'd["metric"]')"
  tools="$(printf '%s' "$f" | jget 'd.get("allowed_tools") or "Read,Grep,Glob"')"
  routes="$(printf '%s' "$f" | jget '" ".join(d.get("routes") or [])')"
  day="$(date -u +%Y-%m-%d)"
  num="$(next_intent_number)"
  slug="auto-${metric//_/-}-$day"
  branch="maintain/$slug"

  git checkout -q -B "$branch" "origin/$DEFAULT_BRANCH" 2>/dev/null || git checkout -q -B "$branch"

  fix_note="Do not modify any file."
  [[ "$action" == "propose" && "$routes" == *pull_request* ]] && \
    fix_note="If, and only if, a minimal low-risk fix is obvious (e.g. quarantining one flaky test), make it in the working tree; otherwise change nothing."

  if [[ "$action" == "report" ]]; then
    out="monitoring/reports/$day-$metric.md"
    ask="Write a concise report for engineering leadership: what drifted, since when, likely causes with evidence, and suggested actions. Output only the Markdown report."
  else
    out="intent/$num-$slug/intent.md"
    ask="Write your diagnosis as an intent.md that follows intent/0000-template/intent.md exactly (frontmatter with source: incident, status: draft, author: maintain-loop). Put the anomaly and its evidence under Problem, a proposed outcome, affected systems, constraints and open questions. Output only the Markdown file content."
  fi
  mkdir -p "$(dirname "$out")"

  claude -p "A control band was breached. Finding (JSON): $f
Investigate the likely cause using the tools you have (CI logs, recent commits, PRs). $fix_note
$ask" --allowedTools "$tools" --max-turns 25 --output-format text > "$out"

  git add -A
  if git diff --cached --quiet; then echo "respond: $metric produced no changes"; continue; fi
  git -c user.name="maintain-loop[bot]" -c user.email="maintain-loop@users.noreply.github.com" \
    commit -q -m "maintain: $metric breached ($(printf '%s' "$f" | jget 'd["tier"]'), rule $(printf '%s' "$f" | jget 'd["rule"]'))"
  git push -q -f origin "$branch"
  gh pr create --base "$DEFAULT_BRANCH" --head "$branch" \
    --title "maintain: $metric — $(printf '%s' "$f" | jget 'd["tier"]') breach" \
    --body "Opened by the maintain loop (\`.github/workflows/metrics-monitor.yml\`).

Finding:
\`\`\`json
$f
\`\`\`

**Triage (service owner / on-call):** fix now · schedule · dismiss. Dismissals should tune \`monitoring/bands.yaml\`." \
    --label maintain-loop 2>/dev/null || echo "respond: PR for $branch already exists or could not be created"

  # Pre-approved runbooks only.
  for route in $routes; do
    [[ "$route" == runbook:* ]] || continue
    rb="${route#runbook:}"
    wf="$(jget "(d['runbooks'].get('$rb') or {}).get('workflow') or ''" < "$FINDINGS")"
    [[ -z "$wf" ]] && continue
    inputs="$(jget "' '.join(f'-f {k}={v}' for k, v in (d['runbooks']['$rb'].get('inputs') or {}).items())" < "$FINDINGS")"
    echo "respond: triggering pre-approved runbook $rb via $wf $inputs"
    # shellcheck disable=SC2086
    gh workflow run "$wf" $inputs
  done
done
