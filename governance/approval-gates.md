# Approval gates

<!-- TEMPLATE: agreed by engineering leadership, change management and compliance.
Every gate that must survive the move to agent-speed delivery is listed here and enforced
deterministically (hook, branch protection or CI environment), not by memory. -->

Owner: `<head of engineering>` · Last reviewed: `<YYYY-MM-DD>`

| Gate | When | Who approves | What counts as approval | Enforced by | Evidence / log |
|------|------|--------------|-------------------------|-------------|----------------|
| G0 Intent acceptance | intent.md enters Design | Product owner | Merge of the intent PR | CODEOWNERS on `intent/` | Git history |
| G1 Spec approval | spec.md enters Build | Product owner (+ tech lead if risk high) | PR approval; all *Areas of concern* resolved | CODEOWNERS, PR template | PR history |
| G2 Protected changes | Edits to migrations, infra, guardrails | Change management | Approved change ticket in `CHANGE_TICKET` | `.claude/hooks/protected-paths.sh` | Hook log + OTel |
| G3 Production release | Deploy/rollback to production | Named release manager | Release ticket in `RELEASE_APPROVAL` **and** reviewer on the `production` environment | `.claude/hooks/production-gate.sh`, `deploy.yml` environment | Hook log, deployment history |
| G4 Merge | Any PR into main | Code owner | GitHub approval | Branch protection + CODEOWNERS | PR history |
| G5 Agent configuration | CLAUDE.md, skills, hooks change | Owners + eval pass rate ≥ threshold | PR approval + green `agent-evals` | Required status check | CI history |

## Risk classes
| Class | Examples | Extra approval |
|-------|----------|----------------|
| low | copy change, internal refactor with full test coverage | none |
| medium | new endpoint, schema change behind a flag | tech lead on the spec |
| high | payments, auth, regulated data, migrations, infra | tech lead or architect on spec **and** plan |

## Rules for gates
- A blocked action always prints the reason and the route to approval.
- Gates apply to everyone, including the agent's non-interactive runs, which act under their own identity.
- Non-negotiable gates live in managed settings (`managed-settings/`), not only in project settings.
- Build-time hooks never ask a human (that would stall parallel sessions); approval prompts belong to the gates above.
