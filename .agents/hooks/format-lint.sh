#!/usr/bin/env bash
# Formats and lints the file that was just edited so drift never accumulates.
# Event: after / write. Must stay fast: one file, no test suite.
# Tools are optional: a formatter that is not installed is skipped.
# Lint errors exit 2 so the agent sees them and fixes them straight away.
set -uo pipefail
. "$(dirname "$0")/lib.sh"

file="$(json_get .operation.path)"
[[ -z "$file" || ! -f "$file" ]] && exit 0

has() { command -v "$1" >/dev/null 2>&1; }
lint_out=""

case "$file" in
  *.py)
    has ruff && { ruff format --quiet "$file"; lint_out="$(ruff check --quiet "$file" 2>&1)"; } ;;
  *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs)
    has npx && [[ -f "$PROJECT_ROOT/node_modules/.bin/prettier" ]] && npx --no-install prettier --log-level warn --write "$file"
    has npx && [[ -f "$PROJECT_ROOT/node_modules/.bin/eslint" ]] && lint_out="$(npx --no-install eslint "$file" 2>&1)" ;;
  *.go)
    has gofmt && gofmt -w "$file" ;;
  *.rs)
    has rustfmt && rustfmt --quiet "$file" ;;
  *.tf)
    has terraform && terraform fmt "$file" >/dev/null ;;
  *.sh)
    has shellcheck && lint_out="$(shellcheck -x "$file" 2>&1)" ;;
esac

if [[ -n "$lint_out" ]]; then
  echo "Lint findings in $file — fix them before continuing:" >&2
  printf '%s\n' "$lint_out" | head -40 >&2
  exit 2
fi
exit 0
