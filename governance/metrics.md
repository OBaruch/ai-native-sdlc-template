# SDLC metrics

<!-- TEMPLATE: one leading and one lagging indicator per play. Record the baseline before
adopting a play, then review monthly. Most data already exists in Git, PR metadata, CI, the
incident tracker and the OpenTelemetry export (managed-settings env). -->

| Play | Leading indicator | Lagging indicator | Data source | Baseline | Target | Owner |
|------|-------------------|-------------------|-------------|----------|--------|-------|
| Capture intent | Time first conversation → committed intent.md | Share of intents accepted vs. closed; intent edits after first spec commit | Git history of `intent/` | | hours | Product ops |
| Requirements & design | Time intent.md commit → spec.md commit | spec.md commits after first plan.md commit (rework) | Git log | | | Product owners |
| Plan mode | Share of changes merged from first implementation pass; plan approval → merge time | Rework cycles per change; merged diff still matches plan.md | PR metadata | | | Tech leads |
| AGENTS.md | Repeated mistakes AGENTS.md should have caught | Time to first merged PR for new joiners | Git history, PR history | | | Tech leads |
| Skills | Policy approval → skill merged | PR findings citing each policy (→ 0) | Skill PRs, review comments | | | Policy owners |
| Parallel sessions | Concurrent sessions per engineer with review quality held | Changes merged per engineer per week vs. rework rate | OTel export, PR history | | | Eng managers |
| Feedback loop | First-pass CI success rate for agent-written changes | Review time per PR; change failure rate | CI, PR metadata, incidents | | | Platform |
| Evals | Eval pass rate over time; incident → eval lead time | Regressions caught in CI vs. in production | `agent-evals` runs, incidents | | ≥ threshold | Platform |
| PR review | Time to first review; comments resolved without a human touching the branch | Defects/vulns caught pre-merge vs. escaped | PR history, incidents | | minutes | Tech leads |
| Approval gates | Wait time per gate | Gate violations reaching production | OTel hook decisions, incidents | | | Change mgmt |
| CI/CD | Pipeline failures triaged without paging a human | DORA: deploy frequency, lead time, change failure rate, time to restore | CI logs, deploy tooling | | | Platform |
| Closing the loop | Time band breach → intent.md in triage | Findings that become merged fixes; repeat incidents | detect logs, PR history | | | SRE |
