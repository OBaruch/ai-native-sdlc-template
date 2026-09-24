# Environments and agent autonomy

<!-- TEMPLATE: the agent may act up to the production gate and cannot pass it. -->

| Environment | Agent may | Credentials | Human gate | Rollback |
|-------------|-----------|-------------|------------|----------|
| dev | deploy freely (auto on merge to main) | short-lived, dev-scoped (OIDC) | none | `scripts/rollback.sh dev` |
| staging | deploy and roll back on demand; weekly rollback drill | short-lived, staging-scoped | none / `<optional reviewer>` | `scripts/rollback.sh staging` |
| production | prepare the release (notes, version, checks) | **none standing**; issued only to the approved job | release ticket + required reviewer on the `production` environment | pre-approved `rollback-deploy` runbook, still gated |

## Configuration checklist
- [ ] GitHub environments `dev`, `staging`, `production` created; `production` has required reviewers.
- [ ] Cloud credentials via OIDC per environment; no long-lived secrets in the repo or runners.
- [ ] Deploy / status / rollback exposed to the agent as scoped MCP tools (`.mcp.example.json`).
- [ ] Agent jobs run in `sandbox/` with the egress policy applied.
- [ ] Branch protection on `main`: PR required, code owner review, required checks, no direct pushes (including bots).
