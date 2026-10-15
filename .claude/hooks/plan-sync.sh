#!/usr/bin/env bash
# Generated Claude adapter; policy lives in .agents/hooks.
export SDLC_LEGACY_STATE_DIR="${CLAUDE_PROJECT_DIR:-$PWD}/.claude"
exec python3 "$(dirname "$0")/../../scripts/claude_hook.py" plan-sync
