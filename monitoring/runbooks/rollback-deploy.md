# Runbook: rollback-deploy

Status: **pre-approved** for the maintain loop (listed in `monitoring/bands.yaml > runbooks`).
Owner: `<release manager>` · Last rehearsed in staging: `<YYYY-MM-DD>` (by `.github/workflows/rollback-drill.yml`)

## When
- The post-deploy 5xx rate (or another release-health metric) breaches 3σ **and** a deployment
  happened inside the detection window.
- Or a human decides to roll back.

## Command
```bash
scripts/rollback.sh <environment> [<version-to-restore>]
```
Without a version it restores the previous successful release.
Through CI: `gh workflow run deploy.yml -f action=rollback -f environment=<env>`.

## Gates
- `dev` / `staging`: runs without approval.
- `production`: the `production` GitHub environment requires a reviewer; locally the
  production gate hook requires `RELEASE_APPROVAL`. The agent may prepare the rollback; a human authorizes it.

## Verify
1. Health check `<URL or command>` returns healthy.
2. The breached metric returns inside its 1σ band within `<N>` minutes.
3. Post the evidence in the incident thread or PR.

## After
- Open or update the incident; write the post-mortem (`/postmortem <id>`).
- Add a regression eval under `evals/`.
