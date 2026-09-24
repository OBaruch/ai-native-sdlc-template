# AI-native SDLC playbook — lesson map

This template implements the practices from Anthropic Academy's course
[The AI-native SDLC playbook](https://academy.claude.com/courses/ai-native-sdlc-playbook/).
Read the lessons at the source; this page only maps each one to the files that implement it.

| # | Stage | Lesson | Implemented by |
|---|-------|--------|----------------|
| 1 | — | [Introduction](https://academy.claude.com/courses/ai-native-sdlc-playbook/introduction) | [`README.md`](../../README.md) |
| 2 | Plan | [Capture as intent.md](https://academy.claude.com/courses/ai-native-sdlc-playbook/capture-intent) | `intent/`, `.claude/skills/intent-template/`, `/new-intent`, `.github/ISSUE_TEMPLATE/idea.yml` |
| 3 | Design | [Requirements and design](https://academy.claude.com/courses/ai-native-sdlc-playbook/requirements-and-design) | `intent/0000-template/spec.md`, policy skills, `/write-spec`, `intent-to-spec.yml` |
| 4 | Build | [Plan mode](https://academy.claude.com/courses/ai-native-sdlc-playbook/plan-mode) | `intent/0000-template/plan.md`, `/write-plan`, `plan-sync.sh`, `governance/source-of-truth.md` |
| 5 | Build | [The CLAUDE.md](https://academy.claude.com/courses/ai-native-sdlc-playbook/claude-md) | `CLAUDE.md` |
| 6 | Build | [Skills as institutional knowledge](https://academy.claude.com/courses/ai-native-sdlc-playbook/skills-as-institutional-knowledge) | `.claude/skills/`, build-time hooks, `governance/policy-owners.md` |
| 7 | Build | [Parallel sessions and subagents](https://academy.claude.com/courses/ai-native-sdlc-playbook/parallel-sessions-and-subagents) | `.claude/agents/`, permissions in `.claude/settings.json` |
| 8 | Test | [Give Claude a feedback loop](https://academy.claude.com/courses/ai-native-sdlc-playbook/give-claude-a-feedback-loop) | `Makefile`, `CLAUDE.md > Verifying your work`, `protect-tests.sh`, `require-verification.sh`, `/fix-bug` |
| 9 | Test | [Continuous evals in CI](https://academy.claude.com/courses/ai-native-sdlc-playbook/continuous-evals-in-ci) | `evals/`, `agent-evals.yml` |
| 10 | Deploy | [AI in the PR review loop](https://academy.claude.com/courses/ai-native-sdlc-playbook/ai-in-the-pr-review-loop) | `REVIEW.md`, `CODEOWNERS`, `claude-code-review.yml`, `claude.yml`, `/babysit-pr` |
| 11 | Deploy | [Hooks as approval gates](https://academy.claude.com/courses/ai-native-sdlc-playbook/hooks-as-approval-gates) | `production-gate.sh`, `protected-paths.sh`, `managed-settings/`, `governance/approval-gates.md` |
| 12 | Deploy | [CI/CD integration and deployment](https://academy.claude.com/courses/ai-native-sdlc-playbook/ci-cd-integration-and-deployment) | `ci.yml`, `deploy.yml`, `rollback-drill.yml`, `sandbox/`, `.mcp.example.json`, `scripts/`, `governance/environments.md` |
| 13 | Maintain | [Closing the loop on metrics](https://academy.claude.com/courses/ai-native-sdlc-playbook/closing-the-loop-on-metrics) | `monitoring/`, `metrics-monitor.yml`, `postmortems/`, `/postmortem` |
| 14 | — | [Closing thoughts and resources](https://academy.claude.com/courses/ai-native-sdlc-playbook/closing-thoughts-and-resources) | `managed-settings/README.md`, `governance/` |

## Offline copies (optional, not committed)
`html_to_txt.py` converts lesson pages you saved locally (`html/`) into plain text next to this
file for personal reading. Both are git-ignored: the course content belongs to its authors.
